"""
fixture_dispatch_clarify_and_abstain — exercises §1.5 routing, §4 clarification, §5 abstain.

Reference implementation of the orchestrator's dispatch + clarify-or-abstain
protocol per `references/dispatch-and-profile.md` §1.5 + §4 + §5. Real
orchestrator code must produce identical routing decisions, clarification
prompts, and abstain reasons for the inputs below.

Run:
    python3 skills/tests/fixture_dispatch_clarify_and_abstain/run.py
"""
from __future__ import annotations
import sys
from typing import Any

# ---------------- Canonical slot vocabulary (§1.3) -----------------

# All valid slot keys per dispatch-and-profile.md §1.3. Any slot key not in this
# set on an incoming request → invalid_slot_type per §5.
VALID_SLOTS = frozenset([
    "query_text", "rid", "rid_set", "rid_pair",
    "paper_rid", "reviewer_text_or_rid",
    "comparison_axes",
    "latex_dir", "text_blob", "pdf_path",
    "field_patches", "target_rid",
    "q",
    # optional inputs (sub-skill-declared, e.g. sidecar-reader.question_id) are also valid;
    # for the dispatch fixture we add canonical optional slots here:
    "question_id",
])

# OR-slot groups per §1.5 routing table. Supplying any 2 members of a group → invalid_slot_type.
# Note: contribute is a 3-way OR (latex_dir / text_blob / pdf_path) — pairwise check covers it.
OR_SLOT_PAIRS = [
    frozenset(["latex_dir", "text_blob"]),       # contribute (sidecar-author) — pair 1
    frozenset(["latex_dir", "pdf_path"]),        # contribute — pair 2
    frozenset(["text_blob", "pdf_path"]),        # contribute — pair 3
    frozenset(["query_text", "rid_set"]),        # synthesize_prose (survey-narrative)
]


# ---------------- Canonical routing table (§1.5) -----------------

# Each row: (intent_class, required_slot_set, requested_artifact, skill, multi_row_skill: bool)
# multi_row_skill flag tracks skills with >1 row in §1.5 — clarification needs name+artifact for these.
ROUTING_TABLE = [
    ("discover", frozenset(["query_text"]), "ranked_paper_list", "paper-finder", True),
    ("discover", frozenset(["query_text"]), "bibtex", "paper-finder", True),
    ("extract", frozenset(["rid", "q"]), "answer_json", "sidecar-reader", False),
    ("synthesize_prose", frozenset(["query_text"]), "related_work_paragraph", "survey-narrative", False),  # OR rid_set; both legal per §1.5
    ("synthesize_prose", frozenset(["rid_set"]), "related_work_paragraph", "survey-narrative", False),
    ("synthesize_table", frozenset(["rid_set", "comparison_axes"]), "comparison_table", "survey-table", False),
    ("diff", frozenset(["rid_pair"]), "diff_report", "paper-compare", False),
    ("critique_generate", frozenset(["paper_rid"]), "review_sidecar", "review-sidecar", False),
    ("critique_respond", frozenset(["paper_rid", "reviewer_text_or_rid"]), "rebuttal_doc", "rebuttal-builder", False),
    ("brief_next_steps", frozenset(["query_text"]), "next_step_brief", "next-step-advisor", False),
    ("contribute", frozenset(["latex_dir"]), "knows_yaml", "sidecar-author", True),
    ("contribute", frozenset(["text_blob"]), "knows_yaml", "sidecar-author", True),
    ("contribute", frozenset(["pdf_path"]), "knows_yaml", "sidecar-author", True),
    ("contribute", frozenset(["latex_dir"]), "lint_report", "sidecar-author", True),
    ("contribute", frozenset(["text_blob"]), "lint_report", "sidecar-author", True),
    ("contribute", frozenset(["pdf_path"]), "lint_report", "sidecar-author", True),
    ("inspect_lineage", frozenset(["rid"]), "version_chain_report", "version-inspector", False),
    ("revise_local", frozenset(["target_rid", "field_patches"]), "diff_and_yaml", "sidecar-reviser", False),
]

MULTI_ROW_SKILLS = {row[3] for row in ROUTING_TABLE if row[4]}


# ---------------- Reference dispatch (per §1.5) -----------------

def match_rows(intent_class: str, slot_keys: set[str], requested_artifact: str | None) -> list[tuple]:
    """Find all routing-table rows matching (intent_class, slots, artifact).
    artifact=None matches any artifact (used when caller hasn't specified)."""
    matches = []
    for ic, req_slots, art, skill, multi in ROUTING_TABLE:
        if ic != intent_class:
            continue
        if not req_slots.issubset(slot_keys):
            continue
        if requested_artifact is not None and requested_artifact != art:
            continue
        matches.append((ic, req_slots, art, skill, multi))
    return matches


def dispatch(intent_class: str, slots: dict, requested_artifact: str | None) -> dict:
    """Return one of:
      {action: 'route', skill: <name>, route: <row>}
      {action: 'clarify', candidates: [<skill>...], gap: <field>}
      {action: 'abstain', reason: <code>}
    """
    # §5: missing intent_class
    if intent_class is None or intent_class == "":
        return {"action": "abstain", "reason": "unknown_dispatch_tuple"}

    slot_keys = set(slots.keys())

    # §5: unknown slot keys (not in §1.3 vocabulary) → invalid_slot_type
    unknown = slot_keys - VALID_SLOTS
    if unknown:
        return {"action": "abstain", "reason": f"invalid_slot_type.{sorted(unknown)[0]}"}

    # §5: OR-slot collision (e.g. latex_dir + text_blob both supplied) → invalid_slot_type
    for pair in OR_SLOT_PAIRS:
        if pair.issubset(slot_keys):
            offender = sorted(pair)[1]  # report the second slot as the violator
            return {"action": "abstain", "reason": f"invalid_slot_type.{offender}"}

    matches = match_rows(intent_class, slot_keys, requested_artifact)

    if len(matches) == 0:
        return {"action": "abstain", "reason": "unknown_dispatch_tuple"}

    if len(matches) == 1:
        return {"action": "route", "skill": matches[0][3], "route": matches[0]}

    # >1 match → clarification
    candidates = sorted({m[3] for m in matches})
    if requested_artifact is None:
        return {"action": "clarify", "candidates": candidates, "gap": "requested_artifact"}
    return {"action": "clarify", "candidates": candidates, "gap": "intent_class"}


def resolve_with_reply(initial_decision: dict, reply: dict,
                       original_intent: str | None = None,
                       original_slots: dict | None = None,
                       original_artifact: str | None = None) -> dict:
    """§4.2 — apply a clarification reply. Reply may name skill, artifact, intent_class, or extra slot.

    For artifact/intent_class/slot replies, callers pass the original tuple so the
    reply can be merged and re-dispatched against the canonical routing table.
    """
    if initial_decision["action"] != "clarify":
        return initial_decision  # nothing to resolve

    # §4.2 rule set
    candidates = initial_decision["candidates"]
    if "skill" in reply:
        named = reply["skill"]
        if named not in candidates:
            return {"action": "abstain", "reason": "ambiguous_dispatch_unresolved_after_clarification"}
        if named in MULTI_ROW_SKILLS and "requested_artifact" not in reply:
            # Multi-row skill needs name + artifact per Fix R2-#4
            return {"action": "abstain", "reason": "ambiguous_dispatch_unresolved_after_clarification"}
        return {"action": "route", "skill": named,
                "route": ("from_clarification", named, reply.get("requested_artifact"))}

    # Reply provides missing artifact / intent_class / slot — merge and re-dispatch
    if any(k in reply for k in ("requested_artifact", "intent_class")) or \
       (original_slots is not None and any(k in reply for k in VALID_SLOTS - set(original_slots.keys()))):
        if original_intent is None or original_slots is None:
            # Cannot re-dispatch without original tuple — caller must supply
            return {"action": "abstain", "reason": "ambiguous_dispatch_unresolved_after_clarification"}
        merged_intent = reply.get("intent_class", original_intent)
        merged_slots = {**original_slots, **{k: v for k, v in reply.items() if k in VALID_SLOTS}}
        merged_artifact = reply.get("requested_artifact", original_artifact)
        re_decision = dispatch(merged_intent, merged_slots, merged_artifact)
        # If re-dispatch is still ambiguous, refuse — clarification is bounded to one turn (§4.4)
        if re_decision["action"] == "clarify":
            return {"action": "abstain", "reason": "ambiguous_dispatch_unresolved_after_clarification"}
        return re_decision

    return {"action": "abstain", "reason": "ambiguous_dispatch_unresolved_after_clarification"}


# ---------------- Test cases — 4 paths from §7.5 fixture spec -----------------

def test_path_a_unique_route():
    """Path (a): unique tuple → routes correctly to single skill."""
    decision = dispatch("extract", {"rid": "knows:vaswani/attention/1.0.0", "q": "what dataset?"}, "answer_json")
    assert decision["action"] == "route", f"Expected route, got {decision}"
    assert decision["skill"] == "sidecar-reader", f"Wrong skill: {decision}"
    print("PASS: path (a) — unique tuple routes to sidecar-reader")


def test_path_b_ambiguous_clarify():
    """Path (b): ambiguous tuple → emits clarification once, no silent default."""
    # discover + query_text without specifying artifact → matches both ranked_paper_list AND bibtex
    decision = dispatch("discover", {"query_text": "diffusion privacy"}, None)
    assert decision["action"] == "clarify", f"Expected clarify, got {decision}"
    assert "paper-finder" in decision["candidates"]
    assert decision["gap"] == "requested_artifact", f"Wrong gap: {decision}"
    print("PASS: path (b) — ambiguous tuple emits clarification (no silent default)")


def test_path_c_abstain_after_unresolving_reply():
    """Path (c): ambiguous + non-resolving reply → abstain with structured refusal."""
    initial = dispatch("discover", {"query_text": "diffusion privacy"}, None)
    assert initial["action"] == "clarify"

    # Reply that doesn't name skill/artifact/intent_class
    final = resolve_with_reply(initial, {"vague_text": "i don't know what i want"})
    assert final["action"] == "abstain", f"Expected abstain, got {final}"
    assert final["reason"] == "ambiguous_dispatch_unresolved_after_clarification"
    print("PASS: path (c) — non-resolving reply → abstain (no silent default to most-read-only)")


def test_path_d_resolve_with_artifact():
    """Path (d): ambiguous + resolving reply (specifies artifact) → routes correctly via resolve_with_reply."""
    initial = dispatch("discover", {"query_text": "diffusion privacy"}, None)
    assert initial["action"] == "clarify"

    # Reply specifies the missing artifact — exercise resolve_with_reply, NOT a fresh dispatch call
    resolved = resolve_with_reply(
        initial,
        {"requested_artifact": "bibtex"},
        original_intent="discover",
        original_slots={"query_text": "diffusion privacy"},
        original_artifact=None,
    )
    assert resolved["action"] == "route", f"Expected route via resolve_with_reply, got {resolved}"
    assert resolved["skill"] == "paper-finder"
    print("PASS: path (d) — resolve_with_reply with artifact actually re-dispatches to paper-finder")


def test_no_silent_default():
    """Hard invariant: orchestrator MUST NOT silently route on ambiguous tuple, even if one candidate is most-read-only."""
    initial = dispatch("discover", {"query_text": "x"}, None)
    # Decision must NOT be a silent route to paper-finder despite both candidate rows mapping to paper-finder
    # In this case both rows ARE paper-finder, so candidates list length is 1 — but action is still clarify because the (intent, slots, artifact) tuple is incomplete
    assert initial["action"] == "clarify", f"Hard invariant violated! {initial}"
    print("PASS: hard invariant — no silent default route from ambiguous tuple, even when all candidates share a skill")


def test_unknown_dispatch_tuple():
    """A tuple with valid slots but unknown intent_class → abstain with unknown_dispatch_tuple.

    Note: precedence — invalid_slot_type validation runs BEFORE intent_class lookup,
    so this test must use slots from VALID_SLOTS to reach the unknown_dispatch_tuple branch.
    """
    decision = dispatch("nonexistent_intent", {"query_text": "x"}, "ranked_paper_list")
    assert decision["action"] == "abstain", f"Expected abstain, got {decision}"
    assert decision["reason"] == "unknown_dispatch_tuple", f"Wrong reason: {decision}"
    print("PASS: unknown intent_class (with valid slots) → unknown_dispatch_tuple abstain")


def test_multi_row_skill_clarification_needs_artifact():
    """Per Fix R2-#4: naming a multi-row skill (paper-finder, sidecar-author) without artifact does NOT resolve."""
    initial = dispatch("discover", {"query_text": "x"}, None)
    final = resolve_with_reply(initial, {"skill": "paper-finder"})  # no artifact
    assert final["action"] == "abstain", f"Multi-row skill name alone should not resolve: {final}"
    assert final["reason"] == "ambiguous_dispatch_unresolved_after_clarification"

    # Same but with artifact specified — should resolve
    final2 = resolve_with_reply(initial, {"skill": "paper-finder", "requested_artifact": "bibtex"})
    assert final2["action"] == "route", f"Multi-row skill name + artifact should resolve: {final2}"
    print("PASS: multi-row skill clarification needs name + artifact (per Fix R2-#4)")


def test_single_row_skill_clarification_resolves_by_name():
    """A skill with only 1 row (e.g. sidecar-reader) is resolvable by name alone — no artifact needed."""
    # Construct an ambiguous scenario with a single-row skill in candidates
    # E.g. {paper_rid} could match critique_generate → review-sidecar (single row)
    # But to test, simulate: pretend dispatch returned 2 candidates including sidecar-reader
    fake_initial = {"action": "clarify", "candidates": ["sidecar-reader", "paper-compare"], "gap": "intent_class"}
    final = resolve_with_reply(fake_initial, {"skill": "sidecar-reader"})  # no artifact needed
    assert final["action"] == "route", f"Single-row skill name alone should resolve: {final}"
    print("PASS: single-row skill resolvable by name alone (no artifact required)")


def test_bounded_clarification():
    """§4.4: orchestrator clarifies exactly once — no recursive chains. After 1 turn, route or abstain."""
    initial = dispatch("discover", {"query_text": "x"}, None)
    assert initial["action"] == "clarify"
    final = resolve_with_reply(initial, {"vague_text": "still ambiguous"})
    # After ONE reply, must be terminal (route or abstain), never another clarify
    assert final["action"] in {"route", "abstain"}, f"Recursive clarification detected: {final}"
    print("PASS: clarification is bounded to one turn (§4.4)")


def test_unknown_slot_invalid_slot_type():
    """§5: request contains unknown slot key not declared by §1.3 vocabulary → invalid_slot_type."""
    decision = dispatch("extract", {"rid": "knows:foo/1.0", "q": "what?", "extraneous_key": "val"}, "answer_json")
    assert decision["action"] == "abstain", f"Expected abstain on unknown slot, got {decision}"
    assert decision["reason"].startswith("invalid_slot_type."), f"Wrong reason: {decision}"
    assert "extraneous_key" in decision["reason"]
    print("PASS: unknown slot key triggers invalid_slot_type abstain (Fix C1)")


def test_or_slot_collision_invalid_slot_type():
    """§5 + §1.5: supplying any 2 members of an OR-slot group → invalid_slot_type."""
    # contribute is now 3-way OR (latex_dir / text_blob / pdf_path) — test all 3 pairs
    for slots in [
        {"latex_dir": "/path", "text_blob": "raw"},
        {"latex_dir": "/path", "pdf_path": "/p.pdf"},
        {"text_blob": "raw", "pdf_path": "/p.pdf"},
    ]:
        decision = dispatch("contribute", slots, "knows_yaml")
        assert decision["action"] == "abstain", f"Expected abstain for {slots}, got {decision}"
        assert decision["reason"].startswith("invalid_slot_type."), f"Wrong reason: {decision}"
    print("PASS: 3-way OR-slot collisions (all pairs of latex_dir/text_blob/pdf_path) → invalid_slot_type (Fix C1)")


def test_pdf_path_routes_to_sidecar_author():
    """pdf_path is a first-class contribute slot routing to sidecar-author."""
    # PDF → knows_yaml route
    decision_yaml = dispatch("contribute", {"pdf_path": "/papers/vaswani.pdf"}, "knows_yaml")
    assert decision_yaml["action"] == "route", f"PDF→knows_yaml should route, got {decision_yaml}"
    assert decision_yaml["skill"] == "sidecar-author"

    # PDF → lint_report route
    decision_lint = dispatch("contribute", {"pdf_path": "/papers/vaswani.pdf"}, "lint_report")
    assert decision_lint["action"] == "route", f"PDF→lint_report should route, got {decision_lint}"
    assert decision_lint["skill"] == "sidecar-author"
    print("PASS: pdf_path routes to sidecar-author for both knows_yaml and lint_report artifacts")


# ---------------- Runner -----------------

if __name__ == "__main__":
    tests = [
        test_path_a_unique_route,
        test_path_b_ambiguous_clarify,
        test_path_c_abstain_after_unresolving_reply,
        test_path_d_resolve_with_artifact,
        test_no_silent_default,
        test_unknown_dispatch_tuple,
        test_multi_row_skill_clarification_needs_artifact,
        test_single_row_skill_clarification_resolves_by_name,
        test_bounded_clarification,
        test_unknown_slot_invalid_slot_type,
        test_or_slot_collision_invalid_slot_type,
        test_pdf_path_routes_to_sidecar_author,
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
