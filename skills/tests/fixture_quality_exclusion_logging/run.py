"""
fixture_quality_exclusion_logging — exercises G2' (skill-declared quality policy) + §6 manifest visibility.

Reference implementation of the orchestrator's quality filter per
`references/dispatch-and-profile.md` §3.4. Real orchestrator code must produce
identical exclusion lists with policy_field + actual values.

Run:
    python3 skills/tests/fixture_quality_exclusion_logging/run.py
"""
from __future__ import annotations
import sys
from typing import Any

# Canonical enum from knows-record-0.9.json coverage.statements
COVERAGE_STATEMENTS_ENUM = {"exhaustive", "main_claims_only", "key_claims_and_limitations", "partial"}


# ---------------- Strict quality policy (sidecar-reader / paper-finder shape) -----------------

STRICT_POLICY = {
    "require_lint_passed": True,
    "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations"],  # excludes "partial"
    "min_statements": 5,
}


# ---------------- Synthetic corpus -----------------

# Mix of records: passing, lint-failing, partial-coverage, too-few-statements
CORPUS: list[dict[str, Any]] = [
    {"rid": "rec:good1", "profile": "paper@1", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 12}},
    {"rid": "rec:good2", "profile": "paper@1", "lint_passed": True, "coverage_statements": "main_claims_only", "stats": {"stmt_count": 7}},
    {"rid": "rec:good3", "profile": "paper@1", "lint_passed": True, "coverage_statements": "key_claims_and_limitations", "stats": {"stmt_count": 5}},  # exactly min
    {"rid": "rec:lint_fail", "profile": "paper@1", "lint_passed": False, "coverage_statements": "exhaustive", "stats": {"stmt_count": 10}},
    {"rid": "rec:partial_cov", "profile": "paper@1", "lint_passed": True, "coverage_statements": "partial", "stats": {"stmt_count": 8}},
    {"rid": "rec:too_few", "profile": "paper@1", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 3}},
    {"rid": "rec:zero", "profile": "paper@1", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 0}},
]


# ---------------- Reference filter (per §2.2) -----------------

def quality_filter_reason(record: dict[str, Any], policy: dict[str, Any]) -> dict | None:
    """Return None if record passes quality filter; else dict {policy_field, actual} per §2.2 dropped_quality."""
    # Check 1: lint_passed
    if policy["require_lint_passed"] and not record.get("lint_passed", False):
        return {"policy_field": "require_lint_passed", "actual": record.get("lint_passed", False)}

    # Check 2: coverage_statements in allowed set
    cov = record.get("coverage_statements")
    if cov not in policy["allowed_coverage"]:
        return {"policy_field": "allowed_coverage", "actual": cov}

    # Check 3: stmt_count >= min
    stmt_count = record.get("stats", {}).get("stmt_count", 0)
    if stmt_count < policy["min_statements"]:
        return {"policy_field": "min_statements", "actual": stmt_count}

    return None


def apply_quality(records: list[dict], policy: dict) -> tuple[list, list]:
    """Returns (kept, dropped_with_reason). Order of checks matches §2.2 (lint → coverage → count)."""
    kept, dropped = [], []
    for r in records:
        reason = quality_filter_reason(r, policy)
        if reason is None:
            kept.append(r)
        else:
            dropped.append({"rid": r["rid"], **reason})
    return kept, dropped


# ---------------- Test cases -----------------

def test_lint_passed_filter():
    """Records with lint_passed=False are dropped with policy_field=require_lint_passed."""
    kept, dropped = apply_quality(CORPUS, STRICT_POLICY)
    lint_drops = [d for d in dropped if d["policy_field"] == "require_lint_passed"]
    assert len(lint_drops) == 1, f"Expected 1 lint_passed drop, got {len(lint_drops)}: {lint_drops}"
    assert lint_drops[0]["rid"] == "rec:lint_fail"
    assert lint_drops[0]["actual"] is False
    print("PASS: lint_passed=False record dropped, manifest entry has actual=False")


def test_allowed_coverage_filter():
    """Records with coverage_statements not in allowed_coverage are dropped (after lint passes)."""
    kept, dropped = apply_quality(CORPUS, STRICT_POLICY)
    cov_drops = [d for d in dropped if d["policy_field"] == "allowed_coverage"]
    assert len(cov_drops) == 1, f"Expected 1 coverage drop, got {cov_drops}"
    assert cov_drops[0]["rid"] == "rec:partial_cov"
    assert cov_drops[0]["actual"] == "partial"
    print("PASS: partial-coverage record dropped, manifest entry has actual='partial'")


def test_min_statements_filter():
    """Records with stmt_count < min_statements are dropped."""
    kept, dropped = apply_quality(CORPUS, STRICT_POLICY)
    stmt_drops = [d for d in dropped if d["policy_field"] == "min_statements"]
    assert len(stmt_drops) == 2, f"Expected 2 min_statements drops (3 and 0), got {stmt_drops}"
    rids_with_actuals = sorted([(d["rid"], d["actual"]) for d in stmt_drops])
    assert rids_with_actuals == [("rec:too_few", 3), ("rec:zero", 0)], f"Got {rids_with_actuals}"
    print("PASS: stmt_count below min dropped, manifest entries have actual values")


def test_kept_records_complete():
    """Only the 3 fully-passing records survive all 3 checks."""
    kept, _ = apply_quality(CORPUS, STRICT_POLICY)
    kept_rids = {r["rid"] for r in kept}
    assert kept_rids == {"rec:good1", "rec:good2", "rec:good3"}, f"Got {kept_rids}"
    print("PASS: only fully-compliant records reach skill body (3 of 7)")


def test_skill_body_never_sees_excluded():
    """Hard invariant from §2.2: skill body NEVER sees a record that failed quality_policy."""
    kept, dropped = apply_quality(CORPUS, STRICT_POLICY)
    dropped_rids = {d["rid"] for d in dropped}
    kept_rids = {r["rid"] for r in kept}
    assert dropped_rids.isdisjoint(kept_rids), "Excluded record leaked into kept set!"
    print("PASS: skill body never sees an excluded record (G2' hard invariant)")


def test_check_ordering():
    """Order of checks must match §2.2: lint → coverage → count.
    A record failing multiple checks is reported with the FIRST failure encountered."""
    multi_fail = {
        "rid": "rec:multi_fail",
        "profile": "paper@1",
        "lint_passed": False,           # fails check 1
        "coverage_statements": "partial", # would fail check 2
        "stats": {"stmt_count": 1},     # would fail check 3
    }
    reason = quality_filter_reason(multi_fail, STRICT_POLICY)
    assert reason["policy_field"] == "require_lint_passed", f"Expected lint check fired first, got {reason}"
    print("PASS: multi-failure record reports first-failure reason (lint dominates)")


def test_manifest_quality_exclusions_shape():
    """Manifest's quality_exclusions[] must have entries with rid + policy_field + actual per §6.1."""
    _, dropped = apply_quality(CORPUS, STRICT_POLICY)
    for d in dropped:
        assert "rid" in d, f"Missing rid in {d}"
        assert "policy_field" in d, f"Missing policy_field in {d}"
        assert "actual" in d, f"Missing actual in {d}"
        assert d["policy_field"] in {"require_lint_passed", "allowed_coverage", "min_statements"}, f"Unknown policy_field: {d}"
    print(f"PASS: all {len(dropped)} quality_exclusions entries have correct manifest shape")


def test_lenient_policy_admits_more():
    """A skill with lenient policy (e.g. sidecar-author) admits records that strict policy rejects."""
    lenient = {
        "require_lint_passed": False,
        "allowed_coverage": ["exhaustive", "main_claims_only", "key_claims_and_limitations", "partial"],
        "min_statements": 0,
    }
    kept, _ = apply_quality(CORPUS, lenient)
    assert len(kept) == len(CORPUS), f"Lenient policy should admit all {len(CORPUS)}, got {len(kept)}"
    print("PASS: lenient policy admits all records (no exclusions)")


# ---------------- Runner -----------------

if __name__ == "__main__":
    tests = [
        test_lint_passed_filter,
        test_allowed_coverage_filter,
        test_min_statements_filter,
        test_kept_records_complete,
        test_skill_body_never_sees_excluded,
        test_check_ordering,
        test_manifest_quality_exclusions_shape,
        test_lenient_policy_admits_more,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL: {t.__name__} — {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    sys.exit(1 if failed else 0)
