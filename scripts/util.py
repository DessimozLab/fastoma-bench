from __future__ import annotations
import json, subprocess, time, pathlib, shlex
from typing import Dict, Any, List


def run_cmd(cmd: List[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)


def timed_run(cmd: List[str], cwd: str | None = None) -> Dict[str, Any]:
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    t1 = time.time()
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "wall_sec": t1 - t0,
        "cmd": " ".join(shlex.quote(c) for c in cmd),
    }


def append_json_record(file_path: pathlib.Path, record: Dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        data = json.loads(file_path.read_text())
        if not isinstance(data, list):
            data = [data]
        data.append(record)
    else:
        data = [record]
    file_path.write_text(json.dumps(data, indent=2))