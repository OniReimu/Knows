#!/usr/bin/env python3
"""Verify sidecar metadata against external sources (CrossRef, arXiv).

Checks that DOIs, titles, venues, and years in a .knows.yaml are not fabricated.
Requires: requests, pyyaml (pip install requests pyyaml)

Usage:
  python3 verify_metadata.py paper.knows.yaml
  python3 verify_metadata.py --doi-only paper.knows.yaml    # only check DOI resolution
  python3 verify_metadata.py --title-search paper.knows.yaml # search CrossRef by title if no DOI
"""

import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

CROSSREF_API = "https://api.crossref.org/works"
ARXIV_API = "http://export.arxiv.org/api/query"
S2_API = "https://api.semanticscholar.org/graph/v1/paper"
OPENALEX_API = "https://api.openalex.org/works"
HEADERS = {
    "User-Agent": "knows-verify/1.0 (mailto:knows@knows.academy; sidecar metadata verification)"
}


def _load_env_file(path: Path) -> dict:
    """Parse a .env file without external dependencies."""
    env = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip("\"'")
    except FileNotFoundError:
        pass
    return env


def get_openalex_key() -> Optional[str]:
    """Load OpenAlex API key.

    Priority: OPENALEX_API_KEY env var → ~/.claude/.env → ./.env

    DOI lookups are free without a key. A key enables title search
    (1000 queries/day free). Register at https://openalex.org.
    """
    import os
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        return key
    key = _load_env_file(Path.home() / ".claude" / ".env").get("OPENALEX_API_KEY")
    if key:
        return key
    return _load_env_file(Path(".env")).get("OPENALEX_API_KEY")


def _parse_openalex_work(work: dict) -> dict:
    authors = [
        a.get("author", {}).get("display_name", "")
        for a in work.get("authorships", [])
        if a.get("author", {}).get("display_name")
    ]
    source = (work.get("primary_location") or {}).get("source") or {}
    return {
        "title": work.get("title", ""),
        "authors": authors,
        "year": work.get("publication_year"),
        "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
        "venue": source.get("display_name", ""),
        "cited_by_count": work.get("cited_by_count", 0),
        "oa_url": (work.get("open_access") or {}).get("oa_url"),
        "openalex_id": work.get("id", ""),
    }


def resolve_openalex(doi: str, api_key: Optional[str] = None) -> Tuple[Optional[dict], str]:
    """Resolve a DOI via OpenAlex API (free, unlimited single-entity lookup).

    Returns:
        (metadata_dict, status) where status is 'found', 'not_found', or 'error'.
    """
    doi_url = doi if doi.startswith("http") else f"https://doi.org/{doi}"
    params = {"api_key": api_key} if api_key else {}
    try:
        r = requests.get(f"{OPENALEX_API}/{doi_url}", headers=HEADERS,
                         params=params, timeout=15)
        if r.status_code == 200:
            return _parse_openalex_work(r.json()), "found"
        if r.status_code == 404:
            return None, "not_found"
        return None, "error"
    except Exception:
        return None, "error"


def search_openalex_by_title(title: str, api_key: Optional[str] = None) -> Optional[dict]:
    """Search OpenAlex by title (requires API key for reliable access).

    Returns best match or None.
    """
    params = {"search": title, "per-page": "3"}
    if api_key:
        params["api_key"] = api_key
    try:
        r = requests.get(OPENALEX_API, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return _parse_openalex_work(results[0])
        return None
    except Exception:
        return None


def resolve_doi(doi: str) -> Tuple[Optional[dict], str]:
    """Resolve a DOI via CrossRef API.

    Returns:
        (metadata_dict, status) where status is 'found', 'not_found', or 'error'.
    """
    url = f"{CROSSREF_API}/{quote(doi, safe='')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=False)
        # Follow redirects manually to CrossRef only (not arbitrary hosts)
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("Location", "")
            if location.startswith("https://api.crossref.org/"):
                r = requests.get(location, headers=HEADERS, timeout=15, allow_redirects=False)
            else:
                return None, "error"
        if r.status_code == 200:
            return r.json().get("message", {}), "found"
        if r.status_code == 404:
            return None, "not_found"
        return None, "error"
    except requests.exceptions.Timeout:
        return None, "error"
    except Exception:
        return None, "error"


def resolve_arxiv(arxiv_id: str) -> Tuple[Optional[dict], str]:
    """Resolve an arXiv ID via arXiv API.

    Returns:
        (metadata_dict, status) where status is 'found', 'not_found', or 'error'.
        metadata_dict has keys: title, authors, year, categories.
    """
    import xml.etree.ElementTree as ET
    clean_id = arxiv_id.strip().replace("arXiv:", "")
    url = f"{ARXIV_API}?id_list={quote(clean_id, safe='')}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None, "error"
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if not entries:
            return None, "not_found"
        entry = entries[0]
        # Check if arXiv returned an error entry
        id_elem = entry.find("atom:id", ns)
        if id_elem is not None and "api/errors" in (id_elem.text or ""):
            return None, "not_found"
        title_elem = entry.find("atom:title", ns)
        title_text = " ".join((title_elem.text or "").split()) if title_elem is not None else ""
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)
                    if a.find("atom:name", ns) is not None]
        published = entry.find("atom:published", ns)
        year = int(published.text[:4]) if published is not None and published.text else None
        return {"title": title_text, "authors": authors, "year": year}, "found"
    except Exception:
        return None, "error"


def resolve_semantic_scholar(title: str) -> Tuple[Optional[dict], str]:
    """Search Semantic Scholar by title. Covers OpenReview, DBLP, and venues without DOIs.

    Returns:
        (metadata_dict, status) where metadata has title, venue, year, externalIds.
    """
    params = {"query": title, "limit": 3, "fields": "title,venue,year,externalIds,authors"}
    for attempt in range(3):
        try:
            r = requests.get(f"{S2_API}/search", params=params, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                papers = r.json().get("data", [])
                if papers:
                    best = papers[0]
                    return {
                        "title": best.get("title", ""),
                        "venue": best.get("venue", ""),
                        "year": best.get("year"),
                        "externalIds": best.get("externalIds", {}),
                        "authors": [a.get("name", "") for a in best.get("authors", [])],
                    }, "found"
                return None, "not_found"
            if r.status_code == 429:
                time.sleep(3 * (attempt + 1))  # backoff: 3s, 6s, 9s
                continue
            return None, "error"
        except Exception:
            return None, "error"
    return None, "error"


def search_by_title(title: str) -> Optional[dict]:
    """Search CrossRef by title. Returns best match or None."""
    params = {"query.title": title, "rows": 3}
    try:
        r = requests.get(CROSSREF_API, params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            if items:
                return items[0]
        return None
    except Exception:
        return None


def normalize(s: str) -> str:
    """Lowercase, normalize unicode, strip punctuation for fuzzy comparison."""
    # Decompose accents (é → e), then strip non-alphanumeric (unicode-aware)
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s]", "", s.lower(), flags=re.UNICODE).strip()
    return s


def title_similarity(a: str, b: str) -> float:
    """Word overlap similarity with containment boost for subtitles."""
    wa = set(normalize(a).split())
    wb = set(normalize(b).split())
    if not wa or not wb:
        return 0.0
    intersection = len(wa & wb)
    jaccard = intersection / max(len(wa | wb), 1)
    # Containment: if one title is a subset of the other, boost score
    containment = intersection / min(len(wa), len(wb))
    return max(jaccard, containment * 0.9)


def _enrich_cited_artifacts(path: Path, record: dict,
                              openalex_key: Optional[str] = None) -> tuple[int, int]:
    """Auto-enrich artifacts with role in {cited, supporting} that lack
    identifiers/locators/representations. For artifact_type=='paper', search
    OpenAlex by title to fill arxiv/doi/url. For others (benchmark/dataset/
    model/repository/software/website), no auto-source available — log and skip.

    Returns (enriched_count, skipped_count). Mutates record in place + writes
    file when enriched_count > 0."""
    enriched, skipped = 0, 0
    artifacts = record.get("artifacts", [])
    for art in artifacts:
        role = art.get("role")
        if role not in ("cited", "supporting"):
            continue
        # Already has discoverable info — skip
        if art.get("identifiers") or art.get("locators") or art.get("representations"):
            continue
        art_id = art.get("id", "?")
        title = art.get("title", "")
        if not title:
            print(f"  SKIP {art_id}: no title to search by")
            skipped += 1
            continue
        atype = art.get("artifact_type", "other")
        if atype == "paper":
            # Try OpenAlex title search
            meta = search_openalex_by_title(title, openalex_key)
            if meta:
                ids: dict = {}
                if meta.get("doi"):
                    ids["doi"] = meta["doi"]
                if meta.get("arxiv"):
                    ids["arxiv"] = meta["arxiv"]
                if not ids and meta.get("url"):
                    ids["url"] = meta["url"]
                if ids:
                    art["identifiers"] = ids
                    print(f"  ENRICHED {art_id} ({atype}): {list(ids.keys())}")
                    enriched += 1
                else:
                    print(f"  SKIP {art_id}: OpenAlex match found but no doi/arxiv/url")
                    skipped += 1
            else:
                print(f"  SKIP {art_id}: no OpenAlex match for title")
                skipped += 1
        else:
            # Non-paper cited artifacts — no auto-source. Log so user can supply manually.
            print(f"  SKIP {art_id} ({atype}): no auto-enrichment source for type "
                  f"'{atype}' — supply identifiers.url manually (e.g. HuggingFace / GitHub URL)")
            skipped += 1
    if enriched > 0:
        with open(path, "w") as fp:
            yaml.dump(record, fp, sort_keys=False, allow_unicode=True, default_flow_style=False)
        print(f"  WROTE {enriched} enrichment(s) to {path.name}")
    return enriched, skipped


def verify_sidecar(path: Path, doi_only: bool = False, title_search: bool = False,
                    auto_enrich: bool = False, openalex_key: Optional[str] = None,
                    include_cited: bool = False) -> int:
    """Verify a sidecar file. Returns number of issues found."""
    record = yaml.safe_load(path.read_text())
    if not isinstance(record, dict):
        print(f"  ERROR: YAML root is not a mapping")
        return 1

    issues = 0
    title = record.get("title", "")
    venue = record.get("venue", "")
    year = record.get("year")
    venue_type = record.get("venue_type", "")

    # Skip verification for from-idea sidecars
    if venue_type == "in_preparation":
        print(f"\n--- {path.name} ---")
        print(f"  Title: {title[:80]}")
        print(f"  Type:  in_preparation (from-idea sidecar)")
        print(f"  SKIP:  DOI/venue/year verification not applicable for in-preparation records")
        # Only check for accidental fabrication of fields that shouldn't exist
        for art in record.get("artifacts", []):
            ids = art.get("identifiers", {})
            if ids.get("doi") and not str(ids["doi"]).startswith("TODO"):
                print(f"  WARN: in_preparation sidecar has DOI '{ids['doi']}' — should this be published/preprint instead?")
                issues += 1
        return issues

    # Find DOI and arXiv ID from the subject artifact
    subject_ref = record.get("subject_ref", "")
    doi = None
    arxiv_id = None
    for art in record.get("artifacts", []):
        if art.get("id") == subject_ref:
            ids = art.get("identifiers", {})
            if "doi" in ids and ids["doi"] and not str(ids["doi"]).startswith("TODO"):
                doi = ids["doi"]
            if "arxiv" in ids and ids["arxiv"]:
                arxiv_id = ids["arxiv"]
            break
    # Fallback: check first paper/subject artifact
    if not doi and not arxiv_id:
        for art in record.get("artifacts", []):
            if art.get("artifact_type") == "paper" and art.get("role") == "subject":
                ids = art.get("identifiers", {})
                if "doi" in ids and ids["doi"] and not str(ids["doi"]).startswith("TODO"):
                    doi = ids["doi"]
                if "arxiv" in ids and ids["arxiv"]:
                    arxiv_id = ids["arxiv"]
                break

    print(f"\n--- {path.name} ---")
    print(f"  Title: {title[:80]}")
    print(f"  DOI:   {doi or 'NONE'}")
    if arxiv_id:
        print(f"  arXiv: {arxiv_id}")
    print(f"  Venue: {venue or 'NONE'}")
    print(f"  Year:  {year or 'NONE'}")
    if venue_type:
        print(f"  Type:  {venue_type}")

    if doi:
        # Try OpenAlex first (free DOI lookup, richer metadata), fallback to CrossRef
        print(f"\n  Resolving DOI via OpenAlex...")
        oa_meta, oa_status = resolve_openalex(doi, openalex_key)

        resolved_title, resolved_venue, resolved_year, source_label = "", "", None, ""
        if oa_status == "found":
            print(f"  PASS: DOI resolves (OpenAlex)")
            resolved_title = oa_meta.get("title", "")
            resolved_venue = oa_meta.get("venue", "")
            resolved_year = oa_meta.get("year")
            source_label = "OpenAlex"
        else:
            if oa_status == "not_found":
                print(f"  OpenAlex: not found — trying CrossRef...")
            else:
                print(f"  OpenAlex: network error — trying CrossRef...")
            cr_meta, cr_status = resolve_doi(doi)
            if cr_status == "not_found":
                print(f"  FAIL: DOI '{doi}' does not resolve (404) — possibly fabricated")
                issues += 1
            elif cr_status == "error":
                print(f"  WARN: Could not reach CrossRef (network error/timeout) — skipping DOI check")
            else:
                print(f"  PASS: DOI resolves (CrossRef)")
                cr_titles = cr_meta.get("title", [])
                resolved_title = cr_titles[0] if cr_titles else ""
                for ct in cr_meta.get("container-title", []):
                    resolved_venue = ct
                    break
                for dp in cr_meta.get("published", cr_meta.get("issued", {})).get("date-parts", []):
                    if dp and dp[0] is not None:
                        resolved_year = dp[0]
                        break
                source_label = "CrossRef"

        if source_label:
            if doi_only:
                return issues

            # Check title match
            sim = title_similarity(title, resolved_title)
            if sim < 0.5:
                print(f"  WARN: Title mismatch (similarity {sim:.0%})")
                print(f"    Sidecar:  {title[:70]}")
                print(f"    {source_label}: {resolved_title[:70]}")
                issues += 1
            else:
                print(f"  PASS: Title matches (similarity {sim:.0%})")

            # Check venue
            if venue and resolved_venue:
                vsim = title_similarity(venue, resolved_venue)
                if vsim < 0.3:
                    print(f"  WARN: Venue mismatch")
                    print(f"    Sidecar:  {venue}")
                    print(f"    {source_label}: {resolved_venue}")
                    issues += 1
                else:
                    print(f"  PASS: Venue matches (similarity {vsim:.0%})")

            # Check year
            try:
                if year and resolved_year and abs(int(year) - int(resolved_year)) > 1:
                    print(f"  WARN: Year mismatch (sidecar={year}, {source_label}={resolved_year})")
                    issues += 1
                elif resolved_year:
                    print(f"  PASS: Year matches ({resolved_year})")
            except (ValueError, TypeError):
                print(f"  WARN: Could not compare years (sidecar={year}, {source_label}={resolved_year})")

        if doi_only:
            return issues

    elif not doi and arxiv_id:
        # Preprint: verify via arXiv API
        print(f"\n  Resolving arXiv ID via arXiv API...")
        meta, status = resolve_arxiv(arxiv_id)
        if status == "not_found":
            print(f"  FAIL: arXiv ID '{arxiv_id}' does not resolve — possibly fabricated")
            issues += 1
        elif status == "error":
            print(f"  WARN: Could not reach arXiv API — skipping")
        else:
            print(f"  PASS: arXiv ID resolves")
            if doi_only:
                return issues
            # Check title
            cr_title = meta.get("title", "")
            sim = title_similarity(title, cr_title)
            if sim < 0.5:
                print(f"  WARN: Title mismatch (similarity {sim:.0%})")
                print(f"    Sidecar: {title[:70]}")
                print(f"    arXiv:   {cr_title[:70]}")
                issues += 1
            else:
                print(f"  PASS: Title matches (similarity {sim:.0%})")
            # Check year
            cr_year = meta.get("year")
            try:
                if year and cr_year and abs(int(year) - int(cr_year)) > 1:
                    print(f"  WARN: Year mismatch (sidecar={year}, arXiv={cr_year})")
                    issues += 1
                elif cr_year:
                    print(f"  PASS: Year matches ({cr_year})")
            except (ValueError, TypeError):
                pass
        if doi_only:
            return issues

    elif not doi_only and (title_search or auto_enrich):
        # Step 1: Try OpenAlex (if key available — covers both published + preprints)
        if openalex_key:
            print(f"\n  No DOI found. Searching OpenAlex by title...")
            oa_match = search_openalex_by_title(title, openalex_key)
            if oa_match:
                oa_sim = title_similarity(title, oa_match.get("title", ""))
                if oa_sim >= 0.7:
                    print(f"  FOUND (OpenAlex): similarity {oa_sim:.0%}")
                    print(f"    Title: {oa_match['title'][:70]}")
                    oa_doi = oa_match.get("doi", "")
                    oa_venue = oa_match.get("venue", "")
                    oa_year = oa_match.get("year")
                    if oa_doi:
                        print(f"    DOI: {oa_doi}")
                    if oa_venue:
                        print(f"    Venue: {oa_venue}")
                    if oa_year:
                        print(f"    Year: {oa_year}")
                    if auto_enrich and oa_doi:
                        _enrich_sidecar(path, record, oa_doi, oa_venue,
                                        str(oa_year) if oa_year else "")
                    elif auto_enrich and (oa_venue or oa_year):
                        _enrich_sidecar_venue_only(path, record, oa_venue, oa_year)
                    return issues
                else:
                    print(f"  OpenAlex: low similarity ({oa_sim:.0%}), trying CrossRef...")
        else:
            print(f"\n  No DOI found. (Tip: set OPENALEX_API_KEY in ~/.claude/.env for better title search)")

        # Step 2: Try CrossRef (has DOIs for published papers)
        print(f"  Searching CrossRef by title...")
        meta = search_by_title(title)
        cr_doi, cr_venue, cr_year, cr_title, cr_sim = "", "", None, "", 0.0
        if meta:
            cr_titles = meta.get("title", [])
            cr_title = cr_titles[0] if cr_titles else ""
            cr_sim = title_similarity(title, cr_title)
            cr_doi = meta.get("DOI", "")
            for ct in meta.get("container-title", []):
                cr_venue = ct
                break
            for dp in meta.get("published", meta.get("issued", {})).get("date-parts", []):
                if dp and dp[0] is not None:
                    cr_year = dp[0]
                    break

        # Step 2: Try Semantic Scholar (covers OpenReview, DBLP, venues without DOIs)
        s2_meta, s2_status = None, "not_found"
        if cr_sim < 0.7:
            print(f"  CrossRef: {'low similarity (' + f'{cr_sim:.0%})' if meta else 'no results'}")
            print(f"  Searching Semantic Scholar...")
            time.sleep(0.5)
            s2_meta, s2_status = resolve_semantic_scholar(title)

        # Pick the best source
        best_source = None
        if cr_sim >= 0.7 and cr_doi:
            best_source = "crossref"
        elif s2_meta and s2_status == "found":
            s2_title = s2_meta.get("title", "")
            s2_sim = title_similarity(title, s2_title)
            if s2_sim >= 0.7:
                best_source = "s2"

        if best_source == "crossref":
            print(f"  FOUND (CrossRef): similarity {cr_sim:.0%}")
            print(f"    Title: {cr_title[:70]}")
            print(f"    DOI: {cr_doi}")
            if cr_venue:
                print(f"    Venue: {cr_venue}")
            if cr_year:
                print(f"    Year: {cr_year}")
            if auto_enrich and cr_doi:
                _enrich_sidecar(path, record, cr_doi, cr_venue, str(cr_year) if cr_year else "")

        elif best_source == "s2":
            s2_title = s2_meta["title"]
            s2_sim = title_similarity(title, s2_title)
            s2_venue = s2_meta.get("venue", "")
            s2_year = s2_meta.get("year")
            s2_ids = s2_meta.get("externalIds", {})
            s2_doi = s2_ids.get("DOI", "")
            s2_arxiv = s2_ids.get("ArXiv", "")

            print(f"  FOUND (Semantic Scholar): similarity {s2_sim:.0%}")
            print(f"    Title: {s2_title[:70]}")
            if s2_doi:
                print(f"    DOI: {s2_doi}")
            elif s2_arxiv:
                print(f"    arXiv: {s2_arxiv}")
            else:
                print(f"    IDs: {json.dumps(s2_ids)}")
            if s2_venue:
                print(f"    Venue: {s2_venue}")
            if s2_year:
                print(f"    Year: {s2_year}")

            if auto_enrich:
                enrich_doi = s2_doi or ""
                if not enrich_doi and s2_arxiv:
                    # For OpenReview/ICLR papers: store arXiv ID as identifier
                    _enrich_sidecar_arxiv(path, record, s2_arxiv, s2_venue,
                                          s2_year)
                elif enrich_doi:
                    _enrich_sidecar(path, record, enrich_doi, s2_venue,
                                    str(s2_year) if s2_year else "")
                elif s2_venue or s2_year:
                    _enrich_sidecar_venue_only(path, record, s2_venue, s2_year)
        else:
            if meta:
                print(f"  WARN: Best CrossRef match has low similarity ({cr_sim:.0%})")
                print(f"    CrossRef: {cr_title[:70]}")
            if s2_meta:
                s2_title = s2_meta.get("title", "")
                s2_sim = title_similarity(title, s2_title)
                print(f"  WARN: Best S2 match has low similarity ({s2_sim:.0%})")
                print(f"    S2: {s2_title[:70]}")
            if not meta and not s2_meta:
                print(f"  WARN: No results from CrossRef or Semantic Scholar")
            issues += 1

    elif not doi:
        print(f"\n  WARN: No DOI in sidecar. Use --title-search to search by title.")

    # Check for TODO/placeholder values
    for field, value in [("title", title), ("venue", venue)]:
        if value and ("TODO" in value or "FILL" in value or "PLACEHOLDER" in value):
            print(f"  WARN: {field} contains placeholder text: '{value[:50]}'")
            issues += 1

    # Check for TODO DOIs in artifacts (legacy sidecars)
    for art in record.get("artifacts", []):
        art_doi = art.get("identifiers", {}).get("doi", "")
        if art_doi and str(art_doi).startswith("TODO"):
            print(f"  WARN: {art.get('id','?')} has placeholder DOI '{art_doi}' — run with --auto-enrich to fix")
            issues += 1

    # Optional cited/supporting artifact enrichment (--include-cited)
    if include_cited:
        print(f"\n  --include-cited: enriching cited/supporting artifacts...")
        enriched, skipped = _enrich_cited_artifacts(path, record, openalex_key)
        print(f"  Enriched {enriched} artifact(s); skipped {skipped} (no auto-source or no title match)")

    return issues


def _enrich_sidecar(path: Path, record: dict, doi: str,
                     venue: str = "", year: int = None) -> None:
    """Write enriched metadata back to the sidecar file at the CORRECT paths.

    DOI goes to: artifacts[subject].identifiers.doi
    Venue goes to: root.venue (only if currently empty)
    Year goes to: root.year (only if currently empty)
    """
    modified = False
    subject_ref = record.get("subject_ref", "")

    # Find subject artifact and write DOI
    for art in record.get("artifacts", []):
        is_subject = (art.get("id") == subject_ref or
                      (art.get("artifact_type") == "paper" and art.get("role") == "subject"))
        if is_subject:
            if "identifiers" not in art:
                art["identifiers"] = {}
            old_doi = art["identifiers"].get("doi", "")
            if not old_doi or old_doi.startswith("TODO"):
                art["identifiers"]["doi"] = doi
                print(f"  ENRICHED: artifacts[{art['id']}].identifiers.doi = {doi}")
                modified = True
            break

    # Fill venue if empty
    if venue and not record.get("venue"):
        record["venue"] = venue
        print(f"  ENRICHED: venue = {venue}")
        modified = True

    # Fill year if empty
    if year and not record.get("year"):
        record["year"] = year
        print(f"  ENRICHED: year = {year}")
        modified = True

    if modified:
        with open(path, "w") as f:
            yaml.dump(record, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"  Written: {path}")
    else:
        print(f"  No enrichment needed — all fields already populated")


def _enrich_sidecar_arxiv(path: Path, record: dict, arxiv_id: str,
                           venue: str = "", year: int = None) -> None:
    """Write arXiv ID (for papers without DOI, e.g., OpenReview/ICLR)."""
    modified = False
    subject_ref = record.get("subject_ref", "")
    for art in record.get("artifacts", []):
        is_subject = (art.get("id") == subject_ref or
                      (art.get("artifact_type") == "paper" and art.get("role") == "subject"))
        if is_subject:
            if "identifiers" not in art:
                art["identifiers"] = {}
            if not art["identifiers"].get("arxiv"):
                art["identifiers"]["arxiv"] = arxiv_id
                print(f"  ENRICHED: artifacts[{art['id']}].identifiers.arxiv = {arxiv_id}")
                modified = True
            break
    if venue and not record.get("venue"):
        record["venue"] = venue
        print(f"  ENRICHED: venue = {venue}")
        modified = True
    if year and not record.get("year"):
        record["year"] = year
        print(f"  ENRICHED: year = {year}")
        modified = True
    if modified:
        with open(path, "w") as f:
            yaml.dump(record, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"  Written: {path}")


def _enrich_sidecar_venue_only(path: Path, record: dict,
                                venue: str = "", year: int = None) -> None:
    """Fill venue/year only (no DOI or arXiv found)."""
    modified = False
    if venue and not record.get("venue"):
        record["venue"] = venue
        print(f"  ENRICHED: venue = {venue}")
        modified = True
    if year and not record.get("year"):
        record["year"] = year
        print(f"  ENRICHED: year = {year}")
        modified = True
    if modified:
        with open(path, "w") as f:
            yaml.dump(record, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"  Written: {path}")
    else:
        print(f"  No enrichment needed")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Verify sidecar metadata against OpenAlex/CrossRef/arXiv")
    parser.add_argument("files", nargs="+", help="Sidecar YAML files to verify")
    parser.add_argument("--doi-only", action="store_true", help="Only check DOI resolution")
    parser.add_argument("--title-search", action="store_true",
                        help="Search by title if no DOI found (OpenAlex preferred, CrossRef/S2 fallback)")
    parser.add_argument("--auto-enrich", action="store_true",
                        help="Auto-fill DOI/venue/year from external sources into the sidecar "
                        "(writes to artifacts[subject].identifiers.doi, not root level)")
    parser.add_argument("--include-cited", action="store_true",
                        help="Also enrich artifacts with role={cited,supporting} that lack "
                        "identifiers/locators/representations (paper-type via OpenAlex title "
                        "search; non-paper types logged as needing manual URL)")
    parser.add_argument("--openalex-key", default=None,
                        help="OpenAlex API key (or set OPENALEX_API_KEY in ~/.claude/.env)")
    args = parser.parse_args()

    # Load OpenAlex API key
    openalex_key = args.openalex_key or get_openalex_key()
    if openalex_key:
        print("OpenAlex: API key loaded (DOI lookup + title search available)")
    else:
        print("OpenAlex: no API key — DOI lookup is free; title search limited")
        print("  To enable: add OPENALEX_API_KEY=your_key to ~/.claude/.env")
        print("  Register free at: https://openalex.org → Account Settings → API Keys")

    total_issues = 0
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"\n--- {p} ---\n  ERROR: File not found")
            total_issues += 1
            continue
        total_issues += verify_sidecar(p, args.doi_only, args.title_search, args.auto_enrich,
                                       openalex_key, include_cited=args.include_cited)
        time.sleep(0.5)

    print(f"\n{'PASS' if total_issues == 0 else 'FAIL'}: {total_issues} issues")
    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()
