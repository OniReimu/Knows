#!/usr/bin/env python3
"""knows-gen: Generate KnowsRecord scaffold from a LaTeX project.

Extracts:
  - Paper metadata (title, authors from \\title{}, \\author{})
  - Section structure (\\section{}, \\subsection{})
  - BibTeX citations (\\cite{} references → cited artifact stubs)
  - Labels (\\label{} → anchor targets)
  - Tables and figures (\\begin{table}, \\begin{figure} with \\label)

Outputs a YAML scaffold that the author completes manually with
statements, evidence, and relations.

Usage:
  python knows_gen.py path/to/paper/main.tex -o output.knows.yaml
  python knows_gen.py path/to/paper/ -o output.knows.yaml  # auto-find main.tex
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def find_main_tex(project_dir: Path) -> Path | None:
    """Find the main .tex file in a LaTeX project."""
    candidates = ["main.tex", "paper.tex", "manuscript.tex"]
    for name in candidates:
        p = project_dir / name
        if p.exists():
            return p
    # Fall back to any .tex file containing \documentclass
    for tex in sorted(project_dir.glob("*.tex")):
        content = tex.read_text(errors="ignore")
        if r"\documentclass" in content:
            return tex
    return None


def resolve_inputs(main_tex: Path, max_depth: int = 10) -> str:
    """Resolve \\input{} and \\include{} recursively (up to max_depth)."""
    base_dir = main_tex.parent
    content = main_tex.read_text(errors="ignore")
    input_pattern = re.compile(r"\\(?:input|include)\{([^}]+)\}")

    for _ in range(max_depth):
        new_content = content

        def replace_input(match: re.Match) -> str:
            filename = match.group(1).strip()
            if not filename.endswith(".tex"):
                filename += ".tex"
            input_path = base_dir / filename
            if input_path.exists():
                return input_path.read_text(errors="ignore")
            return match.group(0)

        new_content = input_pattern.sub(replace_input, content)
        if new_content == content:
            break
        content = new_content
    return content


# Regex for one level of brace nesting (covers 95%+ of real LaTeX)
_BRACED = r"((?:[^{}]|\{[^{}]*\})*)"


def extract_title(content: str) -> str:
    # Handle \title[short]{long} with optional argument
    m = re.search(r"\\title(?:\[[^\]]*\])?\{" + _BRACED + r"\}", content)
    if not m:
        return "Untitled Paper"
    title = m.group(1).strip()
    # Strip remaining LaTeX commands but keep text
    title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", title)
    return title


def extract_authors(content: str) -> list[str]:
    # Try multiple \author{} blocks first (acmart style)
    multi = re.findall(r"\\author\{" + _BRACED + r"\}", content)
    if len(multi) > 1:
        authors = []
        for raw in multi:
            raw = re.sub(r"\\(?:thanks|inst|textsuperscript|affiliation|email)\{[^}]*\}", "", raw)
            raw = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", raw)
            name = raw.strip().split("\n")[0].strip()
            if name and len(name) > 1:
                authors.append(name)
        return authors if authors else ["Unknown"]

    # Single \author{} block (NeurIPS, IEEE style)
    m = re.search(r"\\author\{" + _BRACED + r"\}", content, re.DOTALL)
    if not m:
        # Try IEEEtran format
        ieee = re.findall(r"\\IEEEauthorblockN\{([^}]+)\}", content)
        if ieee:
            return [a.strip() for a in ieee if a.strip()]
        return ["Unknown"]
    raw = m.group(1)
    # Strip superscript affiliations like $^{1,2}$ or \textsuperscript{1,2} BEFORE comma split
    raw = re.sub(r"\$\^?\{[^}]*\}\$", "", raw)
    raw = re.sub(r"\$\^\d+\$", "", raw)
    # Strip common noise commands
    raw = re.sub(r"\\(?:thanks|inst|textsuperscript|footnote|email)\{[^}]*\}", "", raw)
    raw = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", raw)
    raw = re.sub(r"\\\\", ",", raw)
    raw = re.sub(r"\\and\b", ",", raw)
    authors = [a.strip() for a in raw.split(",") if a.strip() and len(a.strip()) > 1]
    return authors if authors else ["Unknown"]


def extract_sections(content: str) -> list[dict[str, str]]:
    """Extract section/subsection structure (including starred variants)."""
    sections = []
    pattern = r"\\(section|subsection|subsubsection)\*?\{" + _BRACED + r"\}"
    for m in re.finditer(pattern, content):
        level = m.group(1)
        title = m.group(2).strip()
        title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", title)
        # Look for \label right after
        after = content[m.end() : m.end() + 200]
        label_m = re.search(r"\\label\{([^}]+)\}", after)
        label = label_m.group(1) if label_m else ""
        sections.append({"level": level, "title": title, "label": label})
    return sections


def extract_labels(content: str) -> list[str]:
    """Extract all \\label{} values."""
    return re.findall(r"\\label\{([^}]+)\}", content)


def extract_citations(content: str) -> list[str]:
    """Extract unique citation keys from all cite-like commands."""
    keys: set[str] = set()
    # Covers: \cite, \citep, \citet, \citealt, \citealp, \autocite,
    # \parencite, \textcite, \Cite, \citeauthor, \citeyear, etc.
    for m in re.finditer(r"\\(?:[Cc]ite\w*|autocite|parencite|textcite)\*?(?:\[[^\]]*\])*\{([^}]+)\}", content):
        for key in m.group(1).split(","):
            k = key.strip()
            if k:
                keys.add(k)
    return sorted(keys)


def _extract_caption(block: str) -> str:
    """Extract caption text handling one level of brace nesting."""
    m = re.search(r"\\caption\{" + _BRACED + r"\}", block)
    if not m:
        return ""
    caption = m.group(1)
    caption = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", caption)
    return caption[:120]


def extract_tables(content: str) -> list[dict[str, str]]:
    """Extract table labels and captions."""
    tables = []
    for m in re.finditer(
        r"\\begin\{table\*?\}.*?\\end\{table\*?\}", content, re.DOTALL
    ):
        block = m.group(0)
        label_m = re.search(r"\\label\{([^}]+)\}", block)
        tables.append(
            {
                "label": label_m.group(1) if label_m else "",
                "caption": _extract_caption(block),
            }
        )
    return tables


def extract_figures(content: str) -> list[dict[str, str]]:
    """Extract figure labels and captions."""
    figures = []
    for m in re.finditer(
        r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", content, re.DOTALL
    ):
        block = m.group(0)
        label_m = re.search(r"\\label\{([^}]+)\}", block)
        figures.append(
            {
                "label": label_m.group(1) if label_m else "",
                "caption": _extract_caption(block),
            }
        )
    return figures


def build_scaffold(
    title: str,
    authors: list[str],
    sections: list[dict],
    labels: list[str],
    citations: list[str],
    tables: list[dict],
    figures: list[dict],
    tex_path: Path,
    dense: bool = False,
    replaces: str | None = None,
) -> dict[str, Any]:
    """Build the KnowsRecord scaffold.

    Args:
        dense: When True, generate 15-25 statement stubs including subsections,
               skipped sections (Related Work, Background, Conclusion), figure-
               backed claims, assumptions, and limitations.
        replaces: Optional record_id of a previous sidecar that this one supersedes.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    record: dict[str, Any] = {
        "$schema": "https://knows.dev/schema/record-0.9.json",
        "knows_version": "0.9.0",
        "record_id": f"knows:generated/{tex_path.stem}/1.0.0",
        "profile": "paper@1",
        "subject_ref": "art:paper",
        "title": title,
        "summary": f"Auto-generated sidecar scaffold for '{title}'. "
        "TODO: Complete statements, evidence, and relations manually.",
        "coverage": {"statements": "partial", "evidence": "partial"},
        "license": "CC-BY-4.0",
        "version": {"spec": "0.9.0", "record": "1.0.0", "source": "latex-draft"},
        "freshness": {"as_of": now, "update_policy": "versioned"},
        "provenance": {
            "origin": "machine",
            "actor": {"name": "knows-gen", "type": "tool", "version": "0.9.0"},
            "generated_at": now,
            "method": "extraction",
        },
    }

    if replaces:
        record["replaces"] = replaces

    # Artifacts
    artifacts = [
        {
            "id": "art:paper",
            "artifact_type": "paper",
            "role": "subject",
            "title": title,
            "identifiers": {"arxiv": "TODO"},
            "representations": [
                {
                    "id": "rep:paper-pdf",
                    "media_type": "application/pdf",
                    "locator": {"type": "path", "value": tex_path.stem + ".pdf"},
                }
            ],
        }
    ]
    # Add cited works as artifact stubs
    max_cited = 30
    if len(citations) > max_cited:
        print(f"  Note: {len(citations)} citations found, including first {max_cited} as artifact stubs")
    for i, cite_key in enumerate(citations[:max_cited]):
        artifacts.append(
            {
                "id": f"art:cited-{i+1}",
                "artifact_type": "paper",
                "role": "cited",
                "title": f"TODO: {cite_key}",
                "identifiers": {"doi": f"TODO-{cite_key}"},
                "representations": [],
            }
        )
    record["artifacts"] = artifacts

    # Statement stubs from sections
    _SKIP_SECTIONS_NORMAL = {
        "related work",
        "background",
        "conclusion",
        "acknowledgments",
        "references",
    }
    stmts = []
    stmt_idx = 0

    def _add_claim(stmt_id: str, text: str, locator: str) -> None:
        stmts.append(
            {
                "id": stmt_id,
                "statement_type": "claim",
                "modality": "empirical",
                "text": text,
                "about_ref": "art:paper",
                "status": "asserted",
                "source_anchors": [
                    {
                        "representation_ref": "rep:paper-pdf",
                        "locator_type": "section",
                        "locator": locator,
                    }
                ],
                "confidence": {"claim_strength": "medium", "extraction_fidelity": "medium"},
                "provenance": {
                    "origin": "machine",
                    "actor": {"name": "knows-gen", "type": "tool"},
                    "generated_at": now,
                },
            }
        )

    for sec in sections:
        if dense:
            # Dense: include all sections and subsections (skip only Acknowledgments/References)
            if sec["title"].lower() in ("acknowledgments", "references"):
                continue
            stmt_idx += 1
            level_label = sec["level"].replace("sub", "Sub-")
            _add_claim(
                f"stmt:c{stmt_idx}",
                f"TODO: Claim from {level_label} '{sec['title']}'",
                sec["label"] or sec["title"],
            )
        else:
            # Normal: only top-level sections, skip boilerplate
            if sec["level"] == "section" and sec["title"].lower() not in _SKIP_SECTIONS_NORMAL:
                stmt_idx += 1
                _add_claim(
                    f"stmt:c{stmt_idx}",
                    f"TODO: Main claim from section '{sec['title']}'",
                    sec["label"] or sec["title"],
                )

    if dense:
        # Add figure-backed claim stubs
        for i, fig in enumerate(figures):
            stmt_idx += 1
            caption_hint = f": {fig['caption'][:80]}" if fig["caption"] else ""
            stmts.append(
                {
                    "id": f"stmt:c{stmt_idx}",
                    "statement_type": "claim",
                    "modality": "empirical",
                    "text": f"TODO: Claim supported by Figure {i+1}{caption_hint}",
                    "about_ref": "art:paper",
                    "status": "asserted",
                    "source_anchors": [
                        {
                            "representation_ref": "rep:paper-pdf",
                            "locator_type": "figure",
                            "locator": fig["label"] or f"figure-{i+1}",
                        }
                    ],
                    "confidence": {"claim_strength": "medium", "extraction_fidelity": "medium"},
                    "provenance": {
                        "origin": "machine",
                        "actor": {"name": "knows-gen", "type": "tool"},
                        "generated_at": now,
                    },
                }
            )

        # Add table-backed claim stubs
        for i, tbl in enumerate(tables):
            stmt_idx += 1
            caption_hint = f": {tbl['caption'][:80]}" if tbl["caption"] else ""
            stmts.append(
                {
                    "id": f"stmt:c{stmt_idx}",
                    "statement_type": "claim",
                    "modality": "empirical",
                    "text": f"TODO: Claim supported by Table {i+1}{caption_hint}",
                    "about_ref": "art:paper",
                    "status": "asserted",
                    "source_anchors": [
                        {
                            "representation_ref": "rep:paper-pdf",
                            "locator_type": "table",
                            "locator": tbl["label"] or f"table-{i+1}",
                        }
                    ],
                    "confidence": {"claim_strength": "medium", "extraction_fidelity": "medium"},
                    "provenance": {
                        "origin": "machine",
                        "actor": {"name": "knows-gen", "type": "tool"},
                        "generated_at": now,
                    },
                }
            )

        # Add assumption stubs
        for i in range(1, 3):
            stmts.append(
                {
                    "id": f"stmt:a{i}",
                    "statement_type": "assumption",
                    "modality": "theoretical",
                    "text": f"TODO: Key assumption #{i} underlying the paper's approach",
                    "about_ref": "art:paper",
                    "status": "asserted",
                    "source_anchors": [],
                    "confidence": {"claim_strength": "medium", "extraction_fidelity": "low"},
                    "provenance": {
                        "origin": "machine",
                        "actor": {"name": "knows-gen", "type": "tool"},
                        "generated_at": now,
                    },
                }
            )

        # Add limitation stubs
        for i in range(1, 3):
            stmts.append(
                {
                    "id": f"stmt:l{i}",
                    "statement_type": "limitation",
                    "modality": "empirical",
                    "text": f"TODO: Limitation #{i} of the proposed method or evaluation",
                    "about_ref": "art:paper",
                    "status": "asserted",
                    "source_anchors": [],
                    "confidence": {"claim_strength": "medium", "extraction_fidelity": "low"},
                    "provenance": {
                        "origin": "machine",
                        "actor": {"name": "knows-gen", "type": "tool"},
                        "generated_at": now,
                    },
                }
            )

    record["statements"] = stmts

    # Evidence stubs from tables
    evs = []
    for i, tbl in enumerate(tables):
        evs.append(
            {
                "id": f"ev:t{i+1}",
                "evidence_type": "table_result",
                "summary": f"TODO: {tbl['caption']}" if tbl["caption"] else "TODO: Describe table results",
                "source_anchors": [
                    {
                        "representation_ref": "rep:paper-pdf",
                        "locator_type": "table",
                        "locator": tbl["label"] or f"table-{i+1}",
                    }
                ],
                "observations": [],
                "provenance": {
                    "origin": "machine",
                    "actor": {"name": "knows-gen", "type": "tool"},
                    "generated_at": now,
                },
            }
        )
    # Evidence stubs from figures
    for i, fig in enumerate(figures):
        evs.append(
            {
                "id": f"ev:f{i+1}",
                "evidence_type": "figure",
                "summary": f"TODO: {fig['caption']}" if fig["caption"] else "TODO: Describe figure",
                "source_anchors": [
                    {
                        "representation_ref": "rep:paper-pdf",
                        "locator_type": "figure",
                        "locator": fig["label"] or f"figure-{i+1}",
                    }
                ],
                "observations": [],
                "provenance": {
                    "origin": "machine",
                    "actor": {"name": "knows-gen", "type": "tool"},
                    "generated_at": now,
                },
            }
        )
    record["evidence"] = evs

    # Empty relations (author must fill)
    record["relations"] = []
    record["actions"] = []

    # Extensions
    section_map = {}
    for sec in sections:
        if sec["level"] == "section" and sec["label"]:
            key = sec["title"].lower().replace(" ", "_").replace("&", "and")
            section_map[key] = sec["label"]
    record["extensions"] = {
        "paper": {
            "sections": section_map,
            "extracted_labels": labels,
            "extracted_citations": citations,
        }
    }

    return record


_MODEL_ALIASES: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6-20250514",
    "opus": "claude-opus-4-6-20250514",
}


_LLM_GEN_PROMPT = """\
You are an expert at creating KnowsRecord sidecar files for research papers.

Given the following paper content, generate a complete KnowsRecord YAML sidecar file.

## MANDATORY Root Fields — NEVER omit ANY of these

The following root-level fields are ALL REQUIRED. Omitting any one will cause lint failure:

- $schema: "https://knows.dev/schema/record-0.9.json"
- knows_version: "0.9.0"
- record_id: "knows:generated/<paper-stem>/1.0.0"
- profile: "paper@1"
- subject_ref: "art:paper"
- title: REQUIRED — the exact paper title (NEVER omit)
- summary: REQUIRED — 1-2 sentence description (NEVER omit)
- coverage: REQUIRED — {{statements: "exhaustive", evidence: "key_evidence_only"}}
- license: "CC-BY-4.0"
- version: {{spec: "0.9.0", record: "1.0.0", source: "original"}}
- freshness: {{as_of: "<ISO datetime>", update_policy: "versioned"}}
- provenance: {{origin: "machine", actor: {{name: "knows-gen", type: "tool", version: "0.9.0"}}, \
generated_at: "<ISO datetime>", method: "extraction"}}
- artifacts: REQUIRED — list (at minimum art:paper with role "subject" + cited works)
- statements: list of claims/assumptions/limitations
- evidence: list of evidence items
- relations: list connecting statements to evidence
- actions: [] (empty list)

## Statement fields — EVERY statement MUST have ALL of these (EXACT enum values)
- id: "stmt:c1", "stmt:a1", "stmt:l1", "stmt:m1" etc.
- statement_type: ONLY one of: claim, assumption, limitation, method, question, definition
- modality: ONLY one of: empirical, theoretical, descriptive, normative
- text: concise 1-2 sentence text from the paper
- about_ref: "art:paper"
- status: "asserted"
- source_anchors: [{{representation_ref: "rep:paper-pdf", locator_type: "section", locator: "Section X"}}]
- confidence: {{claim_strength: high/medium/low, extraction_fidelity: high/medium/low}}
- provenance: {{origin: "machine", actor: {{name: "knows-gen", type: "tool"}}, generated_at: "<ISO datetime>"}}

## Evidence fields — EVERY evidence item MUST have ALL of these (EXACT enum values)
- id: "ev:e1", "ev:t1", "ev:f1" etc.
- evidence_type: ONLY one of: table_result, figure, experiment_run, artifact_run, proof, case_study, clinical_trial, observation, survey_result, citation_backed, qualitative_analysis, statistical_test, simulation, other
- summary: REQUIRED — describe what this evidence shows
- source_anchors: [{{representation_ref: "rep:paper-pdf", locator_type: "table"/"figure"/"section", locator: "Table 1"}}]
- observations: REQUIRED — [{{metric: "name", value: 95.0, unit: "%"}}] — metric is REQUIRED in every observation, value MUST be a number, or use qualitative_value for text
- provenance: REQUIRED — {{origin: "machine", actor: {{name: "knows-gen", type: "tool"}}, generated_at: "<ISO datetime>"}}

## Relation fields — EVERY relation MUST have ALL of these (EXACT enum values)
- id: "rel:1", "rel:2" etc.
- subject_ref: "stmt:c1" (what is being supported/challenged)
- predicate: ONLY one of: supported_by, challenged_by, depends_on, limited_by, cites, uses, evaluates_on, implements, documents, same_as, supersedes, retracts
- object_ref: "ev:e1" or "stmt:a1" (what provides the support/challenge)

## Artifact fields
- id: "art:paper", "art:cited-1" etc.
- artifact_type: ONLY one of: paper, repository, dataset, model, benchmark, software, website, other
- role: ONLY one of: subject, supporting, cited
- title, identifiers (ONLY doi/arxiv/isbn/url/custom keys)
- representations: REQUIRED for art:paper — MUST include:
  [{{id: "rep:paper-pdf", media_type: "application/pdf", locator: {{type: "path", value: "<paper-stem>.pdf"}}}}]
  This is critical — source_anchors reference "rep:paper-pdf", so it MUST exist.

## Coverage values
- statements: ONLY one of: exhaustive, main_claims_only, partial, key_claims_and_limitations
- evidence: ONLY one of: exhaustive, key_evidence_only, partial

## STRICT SCHEMA RULES (violations cause lint failure)
- Do NOT add any fields not listed above — every object type has additionalProperties:false
- Do NOT invent extra fields like "description", "tags", "notes", "category", "importance" — they WILL fail
- Do NOT add YAML comments (# ...)
- Every observation MUST have "metric" field
- Every provenance MUST have "origin", "actor" (with "name" and "type"), and "generated_at"
- ID prefixes are mandatory: art: (artifacts), stmt: (statements), ev: (evidence), rel: (relations), rep: (representations)
- Empty arrays: emit "actions: []", never omit the key

## Content Rules
- Generate 7-15 statements covering major claims, findings, assumptions, and limitations
- Generate evidence items for all tables, figures, and key experimental results
- Create relations linking every statement to its supporting evidence (aim for 1.5+ relations per statement)
- Use concrete text from the paper, not generic placeholders
- observation.value MUST be a number (float/int), NOT a string. Use qualitative_value for non-numeric

## SELF-CHECK before output
Verify your YAML has ALL of these root keys: $schema, knows_version, record_id, profile, subject_ref, title, summary, coverage, license, artifacts, statements, evidence, relations, actions, provenance, version, freshness.
Verify art:paper has a representations array with rep:paper-pdf.
Verify every statement has: id, statement_type, modality, text, about_ref, status, source_anchors, confidence, provenance.
Verify every evidence has: id, evidence_type, summary, source_anchors, observations, provenance.
Verify every relation has: id, subject_ref, predicate, object_ref.

## Paper Content

{content}

---

Output ONLY valid YAML. No markdown fences, no YAML comments, no explanation, no text before or after the YAML document.
"""


def _generate_with_llm(
    content: str, model_id: str, tex_path: Path, output: Path,
    replaces: str | None = None,
) -> None:
    """Generate a full sidecar using an LLM (Anthropic Claude)."""
    try:
        import anthropic
    except ImportError:
        print("ERROR: anthropic SDK not installed. Install with: pip install anthropic>=0.40")
        print("  Or: pip install knows-sidecar[eval]")
        sys.exit(1)

    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    # Truncate content if it exceeds model context budget.
    # Reserve ~4K tokens for prompt template + ~16K tokens for output = ~20K tokens.
    # Remaining context budget (~180K tokens for Claude models) ≈ 120K chars of content.
    max_chars = 120_000
    truncated = content[:max_chars]
    if len(content) > max_chars:
        truncated += f"\n\n[... truncated, {len(content) - max_chars} chars omitted ...]"

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    paper_stem = tex_path.stem

    prompt = _LLM_GEN_PROMPT.format(content=truncated)
    # Post-substitute concrete values so LLM doesn't emit literal placeholders
    prompt = prompt.replace("<paper-stem>", paper_stem)
    prompt = prompt.replace("<ISO datetime>", now)

    print(f"  Calling {model_id} ({len(truncated)} chars of content)...")
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=model_id,
        max_tokens=16384,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_yaml = message.content[0].text.strip()

    # Strip markdown fences if the model wrapped output
    if raw_yaml.startswith("```"):
        lines = raw_yaml.split("\n")
        # Remove first line (```yaml or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        raw_yaml = "\n".join(lines)

    # Validate the YAML parses
    try:
        record = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        print(f"ERROR: LLM output is not valid YAML: {e}")
        # Write raw output for debugging
        debug_path = output.with_suffix(".raw.yaml")
        debug_path.write_text(raw_yaml)
        print(f"  Raw LLM output saved to: {debug_path}")
        sys.exit(1)

    if not isinstance(record, dict):
        print("ERROR: LLM output parsed but is not a YAML mapping.")
        sys.exit(1)

    # Post-process: inject replaces if provided
    if replaces:
        record["replaces"] = replaces

    # Write the result
    with open(output, "w") as f:
        yaml.dump(record, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    n_stmts = len(record.get("statements", []))
    n_evs = len(record.get("evidence", []))
    n_rels = len(record.get("relations", []))
    print(f"\nLLM-generated sidecar written to: {output}")
    print(f"  {n_stmts} statements, {n_evs} evidence, {n_rels} relations")
    print(f"  Model: {model_id}")
    print(f"  Tokens used: {message.usage.input_tokens} in / {message.usage.output_tokens} out")
    print(f"\nNext: Review the generated content, then run knows-lint to validate.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="knows-gen: Generate KnowsRecord scaffold from LaTeX",
    )
    parser.add_argument("input", type=Path, help="LaTeX main.tex or project directory")
    parser.add_argument("-o", "--output", type=Path, help="Output YAML file")
    parser.add_argument(
        "--dense",
        action="store_true",
        help="Generate dense scaffold (15-25 stmts) for complex papers",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model for AI-powered generation (e.g., haiku, sonnet, opus). "
        "Requires ANTHROPIC_API_KEY env var.",
    )
    parser.add_argument(
        "--replaces",
        type=str,
        help="Record ID of a previous sidecar that this one supersedes",
    )
    args = parser.parse_args()

    input_path = args.input
    if input_path.is_dir():
        tex_path = find_main_tex(input_path)
        if not tex_path:
            print(f"ERROR: No main .tex file found in {input_path}")
            sys.exit(1)
    else:
        tex_path = input_path

    if not tex_path.exists():
        print(f"ERROR: File not found: {tex_path}")
        sys.exit(1)

    print(f"Parsing: {tex_path}")
    content = resolve_inputs(tex_path)

    output = args.output or Path(f"{tex_path.stem}.knows.yaml")

    # LLM-powered generation path
    if args.model:
        model_id = _MODEL_ALIASES.get(args.model, args.model)
        print(f"  Mode: LLM generation (model={model_id})")
        _generate_with_llm(content, model_id, tex_path, output, replaces=args.replaces)
        return

    title = extract_title(content)
    authors = extract_authors(content)
    sections = extract_sections(content)
    labels = extract_labels(content)
    citations = extract_citations(content)
    tables = extract_tables(content)
    figures = extract_figures(content)

    mode = "dense" if args.dense else "normal"
    print(f"  Mode: {mode}")
    print(f"  Title: {title}")
    print(f"  Authors: {', '.join(authors)}")
    print(f"  Sections: {len(sections)}")
    print(f"  Labels: {len(labels)}")
    print(f"  Citations: {len(citations)}")
    print(f"  Tables: {len(tables)}")
    print(f"  Figures: {len(figures)}")

    scaffold = build_scaffold(
        title, authors, sections, labels, citations, tables, figures, tex_path,
        dense=args.dense,
        replaces=args.replaces,
    )

    with open(output, "w") as f:
        yaml.dump(scaffold, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    if args.dense:
        print(f"\nDense scaffold written to: {output}")
        print(f"  Note: Dense mode generates stubs from all sections/subsections,")
        print(f"  figures, tables, plus assumption and limitation stubs.")
    else:
        print(f"\nScaffold written to: {output}")
    print(f"  {len(scaffold['artifacts'])} artifacts ({len(citations)} cited stubs)")
    print(f"  {len(scaffold['statements'])} statement stubs (TODO: complete manually)")
    print(f"  {len(scaffold['evidence'])} evidence stubs ({len(tables)} tables, {len(figures)} figures)")
    print(f"  {len(scaffold.get('relations', []))} relations (TODO: add manually)")
    print(f"\nNext: Complete TODO fields, add relations, then run knows-lint to validate.")


if __name__ == "__main__":
    main()
