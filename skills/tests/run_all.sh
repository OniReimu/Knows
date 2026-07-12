#!/usr/bin/env bash
# Runs all 4 Knows test fixtures (3 orchestrator integration + 1 banned-phrase-list drift guard).
# CI green on all four is a hard prerequisite for v1 release per dispatch-and-profile.md §7.5.

set -euo pipefail
cd "$(dirname "$0")"

FAILED=0
for fixture in fixture_mixed_profile_retrieval fixture_quality_exclusion_logging fixture_dispatch_clarify_and_abstain fixture_banned_phrase_sync; do
    echo "==> $fixture"
    if python3 "$fixture/run.py"; then
        echo "    OK"
    else
        echo "    FAIL"
        FAILED=$((FAILED + 1))
    fi
    echo
done

if [ $FAILED -eq 0 ]; then
    echo "ALL 3 FIXTURES GREEN — v1 orchestration plumbing prerequisite met"
    exit 0
else
    echo "$FAILED FIXTURE(S) FAILED — v1 release blocked"
    exit 1
fi
