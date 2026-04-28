"""
fixture_mixed_profile_retrieval — exercises G7 (Profile Discipline) + §3 (typed co-input slots).

Reference implementation of the orchestrator's profile filter pipeline per
`references/dispatch-and-profile.md` §2.2 + §2.3 + §3.3. Real orchestrator code
must produce identical exclusion lists and abstain reasons for the inputs below.

Run:
    python3 skills/tests/fixture_mixed_profile_retrieval/run.py
"""
from __future__ import annotations
import re
import sys
from typing import Any

PROFILE_RE = re.compile(r"^[a-z_]+@\d+$")


# ---------------- Synthetic corpus -----------------

# Records the hub might return; mix of valid, mismatched, malformed, and missing profiles.
CORPUS: list[dict[str, Any]] = [
    {"rid": "rec:p1", "profile": "paper@1", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 12}},
    {"rid": "rec:p2", "profile": "paper@1", "lint_passed": True, "coverage_statements": "main_claims_only", "stats": {"stmt_count": 8}},
    {"rid": "rec:r1", "profile": "review@1", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 9}},
    {"rid": "rec:r2", "profile": "review@1", "lint_passed": True, "coverage_statements": "main_claims_only", "stats": {"stmt_count": 7}},
    {"rid": "rec:malformed", "profile": "WeirdProfile", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 10}},
    {"rid": "rec:missing", "lint_passed": True, "coverage_statements": "exhaustive", "stats": {"stmt_count": 11}},  # no `profile` key
]


# ---------------- Reference filter (per §2.2 + §2.3) -----------------

def profile_filter_reason(record: dict[str, Any], allowed: set[str]) -> str | None:
    """Return None if record passes profile filter; else reason code per §2.3."""
    prof = record.get("profile")
    if prof is None:
        return None if "unknown" in allowed else "missing"
    if not PROFILE_RE.match(prof):
        return "malformed"
    if prof not in allowed:
        return "not_in_allowed"
    return None


def filter_pool(records: list[dict], allowed: set[str]) -> tuple[list, list]:
    """Single-pool filter. Returns (kept, dropped_with_reason)."""
    kept, dropped = [], []
    for r in records:
        reason = profile_filter_reason(r, allowed)
        if reason is None:
            kept.append(r)
        else:
            dropped.append({"rid": r.get("rid", "?"), "raw_profile": r.get("profile"), "reason": reason})
    return kept, dropped


def split_co_input_slots(records: list[dict], co_inputs: dict[str, str]) -> dict[str, list]:
    """Split a flat hits list into typed slots keyed by profile, per §3."""
    slots: dict[str, list] = {name: [] for name in co_inputs}
    for r in records:
        for slot_name, slot_profile in co_inputs.items():
            if r.get("profile") == slot_profile:
                slots[slot_name].append(r)
    return slots


# ---------------- Test cases -----------------

def test_single_input_paper_only():
    """sidecar-reader-style: accepts_profiles=[paper@1] → only paper@1 records pass."""
    kept, dropped = filter_pool(CORPUS, {"paper@1"})
    kept_rids = {r["rid"] for r in kept}
    assert kept_rids == {"rec:p1", "rec:p2"}, f"Expected only paper@1, got {kept_rids}"

    # Drop reasons must distinguish missing/malformed/not_in_allowed
    by_reason = {}
    for d in dropped:
        by_reason.setdefault(d["reason"], []).append(d["rid"])
    assert set(by_reason.get("not_in_allowed", [])) == {"rec:r1", "rec:r2"}, f"review@1 should be not_in_allowed: {by_reason}"
    assert by_reason.get("malformed") == ["rec:malformed"], f"malformed list: {by_reason}"
    assert by_reason.get("missing") == ["rec:missing"], f"missing list: {by_reason}"
    print("PASS: single_input paper@1 only — review@1 never enters working set")


def test_single_input_unknown_optin():
    """A skill declaring accepts_profiles=[paper@1, unknown] should also accept records with missing profile."""
    kept, dropped = filter_pool(CORPUS, {"paper@1", "unknown"})
    kept_rids = {r["rid"] for r in kept}
    assert kept_rids == {"rec:p1", "rec:p2", "rec:missing"}, f"Expected paper@1 + missing-profile opt-in, got {kept_rids}"
    # Malformed is still excluded — `unknown` opt-in does NOT cover malformed values
    assert any(d["rid"] == "rec:malformed" and d["reason"] == "malformed" for d in dropped)
    print("PASS: unknown sentinel opt-in covers missing-profile but NOT malformed-profile")


def test_multi_input_typed_slots():
    """rebuttal-builder-style: co_inputs={paper: paper@1, review: review@1} → slots filtered independently."""
    slots = split_co_input_slots(CORPUS, {"paper": "paper@1", "review": "review@1"})
    paper_rids = {r["rid"] for r in slots["paper"]}
    review_rids = {r["rid"] for r in slots["review"]}
    assert paper_rids == {"rec:p1", "rec:p2"}, f"paper slot: {paper_rids}"
    assert review_rids == {"rec:r1", "rec:r2"}, f"review slot: {review_rids}"
    # Critical invariant: no cross-contamination
    assert paper_rids.isdisjoint(review_rids), "paper and review slots must NEVER share a record"
    print("PASS: co_input slots filtered independently, no cross-contamination")


def test_empty_slot_raises_missing_co_input():
    """If a co_input slot ends up empty, abstain reason is missing_co_input.<slot_name>."""
    # Corpus with no review records
    paper_only = [r for r in CORPUS if r.get("profile") == "paper@1"]
    slots = split_co_input_slots(paper_only, {"paper": "paper@1", "review": "review@1"})
    abstain_slot = next((name for name, recs in slots.items() if not recs), None)
    assert abstain_slot == "review", f"Expected review slot empty, got {abstain_slot}"
    abstain_reason = f"missing_co_input.{abstain_slot}"
    assert abstain_reason == "missing_co_input.review"
    print("PASS: empty co_input slot triggers missing_co_input.review")


def test_manifest_exclusion_lists():
    """Manifest must populate excluded_missing_profile + excluded_malformed_profile per §6.1."""
    _, dropped = filter_pool(CORPUS, {"paper@1"})
    excluded_missing = [d["rid"] for d in dropped if d["reason"] == "missing"]
    excluded_malformed = [{"rid": d["rid"], "raw_value": d["raw_profile"]} for d in dropped if d["reason"] == "malformed"]
    assert excluded_missing == ["rec:missing"]
    assert excluded_malformed == [{"rid": "rec:malformed", "raw_value": "WeirdProfile"}]
    print("PASS: manifest exclusion lists populated correctly")


# ---------------- Runner -----------------

if __name__ == "__main__":
    tests = [
        test_single_input_paper_only,
        test_single_input_unknown_optin,
        test_multi_input_typed_slots,
        test_empty_slot_raises_missing_co_input,
        test_manifest_exclusion_lists,
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
