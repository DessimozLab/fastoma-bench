from __future__ import annotations
import os, json, pathlib, datetime, shlex, subprocess, sys
from typing import List, Dict, Any
from parse_metrics import parse_time_v, parse_subhog_fastoma_outputs
from util import append_json_record

MANIFEST = pathlib.Path("datasets/manifest.json")
HISTORY_DIR = pathlib.Path("benchmarks/history")
RESULTS_DIR = pathlib.Path("results")

DOCKER_IMAGE = os.environ.get("FASTOMA_DOCKER_IMAGE", "dessimozlab/fastoma:dev")


def select_datasets(tier: str, group_index: int, group_total: int) -> List[Dict[str, Any]]:
    all_ds = json.loads(MANIFEST.read_text())
    ds = [d for d in all_ds if d["tier"] == tier]
    ds.sort(key=lambda x: x["id"])
    # round-robin partition
    return [d for i, d in enumerate(ds) if i % group_total == group_index]


def get_docker_commit(image: str) -> str:
    """Get git commit from Docker image labels, or "unknown"."""
    try:
        out = subprocess.check_output([
            "docker", "inspect", "--format",
            "{{ index .Config.Labels \"org.opencontainers.image.revision\" }}",
            image
        ], text=True).strip()
        return out or "unknown"
    except subprocess.CalledProcessError:
        return "unknown"


def run_step_docker(dataset: Dict[str, Any], out_dir: pathlib.Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    resource_log = out_dir / "resource.log"

    step = dataset['step']
    input_path = pathlib.Path(dataset['input_path'])
    if step == "omamer":
        cmd_inside = f"omamer search -n 10 --db /data/input/omamer.db --query /data/input/query.fa --out /data/output/query.hogmap"
        step_parse_metric = lambda dataset, out_dir: {}
    elif step == "subhog_inference":
        cmd_inside = f"fastoma-infer-subhogs --input-rhog-folder /data/input --species-tree /data/input/{dataset['sp_tree']} --output-pickles /data/output/pickle_hogs -vv > /data/output/inference.log 2>&1"
        step_parse_metric = parse_subhog_fastoma_outputs
    else:
        raise ValueError(f"Unknown step: {step}")
    print(f"Running step: {step} with command: {cmd_inside}")

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_path.resolve()}:/data/input:ro",
        "-v", f"{out_dir.resolve()}:/data/output",
        "-w", "/data/output",
        DOCKER_IMAGE,
        "/usr/bin/time", "-v", "bash", "-c", cmd_inside
    ]

    print(f"Running {step} in Docker: {' '.join(shlex.quote(c) for c in docker_cmd)}")
    result = subprocess.run(docker_cmd, capture_output=True, text=True)
    # Save stderr (where /usr/bin/time writes resource info)
    resource_log.write_text(result.stderr)

    # Parse metrics
    metrics = parse_time_v(result.stderr)
    # Parse outputs (orthogroups, etc.)
    metrics.update(step_parse_metric(dataset, out_dir))
    metrics["step"] = step
    metrics["fastoma_commit"] = get_docker_commit(DOCKER_IMAGE)
    return metrics


def main():
    tier = os.environ.get("TIER", "tiny")
    group_index = int(os.environ.get("GROUP_INDEX", "0"))
    group_total = int(os.environ.get("GROUP_TOTAL", "1"))

    datasets = select_datasets(tier, group_index, group_total)
    print(f"Selected {len(datasets)} dataset(s) for tier={tier}, group {group_index}/{group_total - 1}")

    for d in datasets:
        ds_id = d["id"]
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"==> Dataset {ds_id}")

        results_ds_dir = RESULTS_DIR / ds_id
        metrics = run_step_docker(d, results_ds_dir)

        # Record results per dataset
        record = {
            "timestamp": ts,
            "dataset": ds_id,
            "host": os.uname().nodename if hasattr(os, "uname") else "gha",
            "env": {
                "python": sys.version.split()[0],
                "docker_image": DOCKER_IMAGE
            },
            "step": d['step'],
            "metrics": metrics,
        }

        out_file = HISTORY_DIR / f"{ds_id}.json"
        append_json_record(out_file, record)
        print(f"✅ Metrics written to {out_file}")


if __name__ == "__main__":
    main()
