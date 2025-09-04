from __future__ import annotations

import itertools
import re
import pathlib
from collections import defaultdict
from typing import Dict, Any, Set

import yaml
import pyham
from pyham.abstractgene import HOG


def parse_elapsed(s: str | None) -> float | None:
    """Convert elapsed time like '0:05.83' or '1:02:15' into seconds."""
    if s is None:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        else:  # already a float or unexpected
            return float(s)
    except Exception:
        return None


def parse_time_v(log_text: str) -> Dict[str, Any]:
    # /usr/bin/time -v output
    def m(p):
        r = re.search(p, log_text)
        return r.group(1) if r else None
    to_float = lambda x: float(x) if x is not None else None
    to_int   = lambda x: int(x) if x is not None else None
    return {
        "user_sec":    to_float(m(r"User time \(seconds\): ([0-9.]+)")),
        "sys_sec":     to_float(m(r"System time \(seconds\): ([0-9.]+)")),
        "max_rss_kb":  to_int(m(r"Maximum resident set size \(kbytes\): (\d+)")),
        "elapsed_sec": parse_elapsed(m(r"Elapsed \(wall clock\) time.*: ([0-9:.]+)")),  # optional
    }


def check_subhog_assertions(ham: pyham.Ham, assert_file: pathlib.Path) -> Dict[str, Any]:
    """
        Validate subHOG inference results against expected assertions.

        Args:
            ham: pyham.Ham instance loaded with inference orthoxml.
            assert_file: Path to YAML file with assertions.

        Returns:
            metrics dict with pass/fail counts and violations.
    """
    metrics = {
        "n_groups": 0,
        "n_assertions": 0,
        "n_passed": 0,
        "n_failed": 0,
        "violations": [],
        "overlaps": []
    }
    assertions = yaml.safe_load(assert_file.read_text())

    def _get_groups_for_reference_geneset(grp: set[str], complete: bool = False) -> Dict[HOG, Set[str]]:
        found = defaultdict(set)
        for m in grp:
            try:
                gene = ham.get_genes_by_external_id(m)[0]
                group, by_dup = gene.search_ancestor_hog_in_ancestral_genome(anc_genome)
                if group is not None:
                    found[group].add(m)
            except KeyError:
                pass
        if complete:
            for group in found:
                all_grp_members = group.get_all_descendant_genes()
                found[group].update((x.prot_id for x in all_grp_members))
        return found

    def _compare_group_sets(expected: set[str], found: Dict[HOG, Set[str]], name: str|None = None) -> None:
        """ Compare expected and found group sets.

        expected is always a single set with protein IDs. The found one can be split into multiple groups.

        The function updates metrics dict with pass/fail counts and violations."""
        if name is None:
            name = "main"
        if len(found) == 1:
            actual = found.popitem()[1]
            if actual == expected:
                metrics["n_passed"] += 1
            else:
                metrics["n_failed"] += 1
                missing = expected - actual
                extra = actual - expected
                metrics["violations"].append(
                    {"level": level, "name": name, "error": f"Protein Sets are not identical: missing {sorted(missing)}; extra {sorted(extra)}"}
                )
            metrics["overlaps"].append({"level": level, "name": name,  "venn": (len(expected-actual), len(actual & expected), len(actual-expected))})
        else:
            metrics["n_failed"] += 1
            metrics["violations"].append(
                {"level": level, "name": name,
                 "error": f"Split into {len(found)} groups: {len(expected)} members, found {sum(len(z) for z in found.values())}"}
            )
            metrics["overlaps"].append(
                {"level": level, "name": name, "venn":
                   (len(expected),
                    max([0, *(len(z & expected) for z in found.values())]),
                    len(set.union(*found.values()) - expected))
                })

    for grp in assertions.get('groups', []):
        metrics["n_groups"] += 1
        level = grp["level"]
        anc_genome = ham.get_ancestral_genome_by_name(level)
        if anc_genome is None:
            metrics["n_failed"] += 1
            metrics["violations"].append(
                {"group": level, "error": f"Ancestral genome {level} not found"}
            )
            continue

        if "members" in grp:
            expected = set(grp["members"])
            found = _get_groups_for_reference_geneset(expected, grp.get("complete", False))
            _compare_group_sets(expected, found)
        # TODO: same for subgroups
        elif "subgroups" in grp:
            subgroups = grp["subgroups"]
            groups_per_subgroups = []
            for i, subgrp in enumerate(subgroups, start=1):
                subgrp["members"] = set(subgrp["members"])
                found = _get_groups_for_reference_geneset(subgrp["members"], subgrp.get("complete", False))
                _compare_group_sets(subgrp["members"], found, subgrp.get("name", f"subgroup_{i}"))
                groups_per_subgroups.append(found)
            # check for overlaps between subgroups
            for i, j in itertools.combinations(range(len(subgroups)), 2):
                grs1 = groups_per_subgroups[i]
                grs2 = groups_per_subgroups[j]
                if len(set(grs1.keys()) & set(grs2.keys())) > 0:
                    metrics["n_failed"] += 1
                    metrics["violations"].append({
                        "level": level, "name": "subgroup_overlap",
                        "error": f'Subgroups overlap between {subgroups[i].get("name", f"subgroup_{i}")} and '
                                 f'{subgroups[j].get("name", f"subgroup_{j}")}: '
                                 f'{len(set(grs1.keys()) & set(grs2.keys()))} common HOGs'
                    })
    return metrics


def parse_subhog_fastoma_outputs(dataset: Dict[str, Any], outdir: pathlib.Path) -> Dict[str, Any]:
    metrics = {}
    with open(outdir / "inference.log", "rt") as f:
        for line in f:
            if m := re.search(r"placed (?P<placed>\d+) out of (?P<kept>\d+) proteins .*\. (?P<total>\d+) proteins in original roothog", line):
                metrics["fraction_placed"] = float(m.group("placed")) / float(m.group("total"))
    input_path = pathlib.Path(dataset["input_path"])
    sp_tree = input_path / dataset["sp_tree"]
    orthxml = next(outdir.glob("ortho_*.orthoxml"))
    ham = pyham.Ham(hog_file=str(orthxml), tree_file=str(sp_tree), tree_format="newick", use_internal_name=True)
    metrics.update(check_subhog_assertions(ham, input_path / "asserted.yml"))
    return metrics

