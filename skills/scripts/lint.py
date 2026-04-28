#!/usr/bin/env python3
"""Inline Knows sidecar linter — no pip install needed beyond pyyaml + jsonschema.

Usage:
  python3 lint.py <sidecar.knows.yaml>
  python3 lint.py <sidecar1.yaml> <sidecar2.yaml> ...

The JSON Schema is resolved relative to this script's location at ../references/knows-record-0.9.json.
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)


def find_schema() -> Path:
    """Resolve schema path relative to this script."""
    candidates = [
        Path(__file__).parent.parent / "references" / "knows-record-0.9.json",
        Path("references/knows-record-0.9.json"),
        Path("skills/references/knows-record-0.9.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    print("ERROR: knows-record-0.9.json not found. Expected in references/ directory.")
    sys.exit(1)


def lint(sidecar: dict, schema: dict) -> tuple[int, int]:
    """Run all checks. Returns (error_count, warning_count)."""
    n_err = 0
    n_warn = 0

    # Check 1: JSON Schema validation
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(sidecar))
    for e in errors:
        print(f"  ERROR: {e.json_path}: {e.message}")
    n_err += len(errors)

    # Collect all IDs
    all_ids: dict[str, str] = {}
    for section in ("artifacts", "statements", "evidence", "relations", "actions"):
        for item in sidecar.get(section, []):
            if "id" in item:
                all_ids[item["id"]] = section
    for art in sidecar.get("artifacts", []):
        for rep in art.get("representations", []):
            if "id" in rep:
                all_ids[rep["id"]] = "representations"

    rep_ids = set()
    for art in sidecar.get("artifacts", []):
        for rep in art.get("representations", []):
            if "id" in rep:
                rep_ids.add(rep["id"])

    art_ids = {i["id"] for i in sidecar.get("artifacts", []) if "id" in i}

    # Check 2: Cross-reference integrity
    sr = sidecar.get("subject_ref", "")
    if sr and sr not in art_ids:
        print(f"  ERROR: subject_ref '{sr}' not in artifacts")
        n_err += 1

    for stmt in sidecar.get("statements", []):
        sid = stmt.get("id", "?")
        ar = stmt.get("about_ref", "")
        if ar and ar not in art_ids:
            print(f"  ERROR: {sid}: about_ref '{ar}' not in artifacts")
            n_err += 1
        for cr in stmt.get("citation_refs", []):
            if cr not in art_ids:
                print(f"  WARN: {sid}: citation_ref '{cr}' not in artifacts")
                n_warn += 1
        for anc in stmt.get("source_anchors", []):
            rr = anc.get("representation_ref", "")
            if rr and rr not in rep_ids:
                print(f"  ERROR: {sid}: anchor representation_ref '{rr}' not found")
                n_err += 1

    for ev in sidecar.get("evidence", []):
        eid = ev.get("id", "?")
        for anc in ev.get("source_anchors", []):
            rr = anc.get("representation_ref", "")
            if rr and rr not in rep_ids:
                print(f"  ERROR: {eid}: anchor representation_ref '{rr}' not found")
                n_err += 1

    for rel in sidecar.get("relations", []):
        rid = rel.get("id", "?")
        for field in ("subject_ref", "object_ref"):
            ref = rel.get(field, "")
            if "#" not in ref and ref and ref not in all_ids:
                print(f"  ERROR: {rid}: {field} '{ref}' not found")
                n_err += 1

    for act in sidecar.get("actions", []):
        aid = act.get("id", "?")
        tr = act.get("target_ref", "")
        if tr and tr not in art_ids:
            print(f"  ERROR: {aid}: target_ref '{tr}' not in artifacts")
            n_err += 1

    # Check 3: ID uniqueness
    seen: dict[str, str] = {}
    for section in ("artifacts", "statements", "evidence", "relations", "actions"):
        for item in sidecar.get(section, []):
            iid = item.get("id", "")
            if iid in seen:
                print(f"  ERROR: Duplicate ID '{iid}' (in {section}, first in {seen[iid]})")
                n_err += 1
            else:
                seen[iid] = section

    # Check 3b: Representation ID uniqueness
    for art in sidecar.get("artifacts", []):
        for rep in art.get("representations", []):
            rid = rep.get("id", "")
            if rid in seen:
                print(f"  ERROR: Duplicate ID '{rid}' in representations (first in {seen[rid]})")
                n_err += 1
            elif rid:
                seen[rid] = "representations"

    # Check 4: ID prefix conventions
    prefixes = {
        "artifacts": "art:",
        "statements": "stmt:",
        "evidence": "ev:",
        "relations": "rel:",
        "actions": "act:",
    }
    for section, pfx in prefixes.items():
        for item in sidecar.get(section, []):
            iid = item.get("id", "")
            if iid and not iid.startswith(pfx):
                print(f"  WARN: '{iid}' in {section} missing prefix '{pfx}'")
                n_warn += 1

    # Check 5: citation_intent only valid with cites predicate
    for rel in sidecar.get("relations", []):
        if "citation_intent" in rel and rel.get("predicate") != "cites":
            print(
                f"  WARN: {rel.get('id', '?')}: citation_intent set "
                f"but predicate is '{rel.get('predicate')}', not 'cites'"
            )
            n_warn += 1

    # Check 6: Artifact discoverability
    for art in sidecar.get("artifacts", []):
        if not (art.get("identifiers") or art.get("locators") or art.get("representations")):
            print(f"  WARN: {art.get('id', '?')}: no identifiers/locators/representations")
            n_warn += 1

    return n_err, n_warn


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 lint.py <sidecar.knows.yaml> [...]")
        sys.exit(1)

    schema = json.loads(find_schema().read_text())
    all_passed = True

    for filepath in sys.argv[1:]:
        p = Path(filepath)
        if not p.exists():
            print(f"\n--- {p} ---\n  ERROR: File not found")
            all_passed = False
            continue

        print(f"\n--- {p} ---")
        try:
            sidecar = yaml.safe_load(p.read_text())
        except Exception as e:
            print(f"  ERROR: Failed to parse YAML: {e}")
            all_passed = False
            continue

        if not isinstance(sidecar, dict):
            print("  ERROR: File does not contain a YAML mapping")
            all_passed = False
            continue

        n_err, n_warn = lint(sidecar, schema)
        status = "PASS" if n_err == 0 else "FAIL"
        print(f"{status}: {n_err} errors, {n_warn} warnings")
        if n_err > 0:
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
