#!/usr/bin/env python3
"""Drift guard for the shared banned-phrase lists.

The speculation-tell list is duplicated across several prompt/skill/stance files (the LLM
reads each copy inline, so the duplication is unavoidable). It drifted once — some copies
carried 9 phrases while the authoritative prompt enforced 15 — which silently weakened the
ban in the copies that lagged. This test is a dumb presence check: every file that carries a
full list must contain every phrase. No markdown parsing; just substring membership.
"""
import pathlib
import sys

SKILLS = pathlib.Path(__file__).resolve().parents[2]  # .../skills

SPECULATION_TELLS = [
    "could explore", "might investigate", "promising direction",
    "future work could", "this opens up", "intriguing avenue",
    "underexplored", "ripe for", "ample opportunity",
    "warrant investigation", "worth exploring", "natural next step",
    "low-hanging fruit", "rich vein", "deserves attention",
]
SPECULATION_FILES = [
    "references/next-step-advisor.md",
    "references/next-step-advisor-prompt.md",
    "sub-skills/next-step-advisor/SKILL.md",
    "references/commentary-builder-prompt.md",
    "sub-skills/commentary-builder/SKILL.md",
    "stances/review-prep/SKILL.md",
    "stances/paper-brainstorm/SKILL.md",
]

NOVELTY_INFLATION = [
    "first to", "no prior work", "nobody has", "unprecedented", "entirely new",
    "clearly novel", "highly original", "no one has explored", "novel approach",
]
NOVELTY_FILES = [
    "references/scoop-check.md",
    "references/scoop-check-prompt.md",
    "sub-skills/scoop-check/SKILL.md",
]


def check(label, phrases, files):
    ok = True
    for rel in files:
        text = (SKILLS / rel).read_text(encoding="utf-8")
        missing = [p for p in phrases if p not in text]
        if missing:
            ok = False
            print(f"FAIL [{label}] {rel} is missing: {missing}")
    return ok


passed = check("speculation-tells", SPECULATION_TELLS, SPECULATION_FILES)
passed = check("novelty-inflation", NOVELTY_INFLATION, NOVELTY_FILES) and passed

if passed:
    print("PASS: banned-phrase lists are in sync across all copies")
    sys.exit(0)
print("banned-phrase lists have drifted — reconcile the copies above")
sys.exit(1)
