#!/usr/bin/env python3
"""Sanitize raw LLM-generated sidecar YAML before lint.

Fixes common generation artifacts:
  1. Strip markdown fences (```yaml ... ```)
  2. Remove XML tag hallucinations (</parameter>, </invoke>, <*>, etc.)
  3. Fix double-quote escaping in YAML strings
  4. Remove non-YAML preamble/postamble text
  5. Fix common YAML syntax errors

Usage:
  python3 sanitize.py raw_output.yaml -o clean.knows.yaml
  python3 sanitize.py raw_output.yaml --in-place
  cat raw_output.yaml | python3 sanitize.py - -o clean.knows.yaml
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)


def sanitize(text: str) -> str:
    """Apply all sanitization passes to raw YAML text."""
    text = strip_bom(text)
    text = remove_control_chars(text)
    text = strip_markdown_fences(text)
    text = remove_xml_tags(text)
    text = fix_yaml_preamble(text)
    text = tabs_to_spaces(text)
    text = fix_trailing_commas(text)
    text = fix_nested_quotes(text)
    text = detect_truncation(text)
    text = warn_duplicate_keys(text)
    return text


def strip_bom(text: str) -> str:
    """Remove UTF-8 BOM if present."""
    return text.lstrip("\ufeff")


def remove_control_chars(text: str) -> str:
    """Remove null bytes and other control characters (except newline/tab)."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def tabs_to_spaces(text: str) -> str:
    """Convert tabs to 2 spaces. YAML forbids tabs for indentation."""
    return text.replace("\t", "  ")


def fix_trailing_commas(text: str) -> str:
    """Remove trailing commas after YAML values (JSON habit).

    Matches: `key: "value",` or `key: 42,` or `- "item",`
    Does NOT touch commas inside quoted strings.
    """
    lines = text.split("\n")
    fixed = []
    for line in lines:
        # Only strip trailing comma if it's outside quotes
        # Simple heuristic: if line ends with , (possibly followed by comment)
        stripped = line.rstrip()
        if stripped.endswith(","):
            # Check it's not inside a quoted value
            # Count unescaped quotes before the trailing comma
            before_comma = stripped[:-1]
            double_quotes = len(re.findall(r'(?<!\\)"', before_comma))
            single_quotes = len(re.findall(r"(?<!\\)'", before_comma))
            # If quotes are balanced, the comma is outside quotes
            if double_quotes % 2 == 0 and single_quotes % 2 == 0:
                line = stripped[:-1]
        fixed.append(line)
    return "\n".join(fixed)


def detect_truncation(text: str) -> str:
    """Detect and warn about truncated YAML output."""
    lines = text.rstrip().split("\n")
    if not lines:
        return text
    last_line = lines[-1].rstrip()
    # Common truncation patterns
    truncation_signs = [
        last_line.endswith(":") and not last_line.strip().startswith("#"),  # key with no value
        last_line.count('"') % 2 == 1,  # unclosed double quote
        last_line.count("'") % 2 == 1,  # unclosed single quote
    ]
    # Check for unclosed brackets/braces in the whole document
    open_brackets = text.count("[") - text.count("]")
    open_braces = text.count("{") - text.count("}")
    if any(truncation_signs) or open_brackets > 0 or open_braces > 0:
        print("  WARN: Output may be truncated (unclosed quotes/brackets or dangling key)", file=sys.stderr)
        if open_brackets > 0:
            # Try to close unclosed brackets
            text = text.rstrip() + "\n" + "]" * open_brackets
        if open_braces > 0:
            text = text.rstrip() + "\n" + "}" * open_braces
    return text


def warn_duplicate_keys(text: str) -> str:
    """Warn about duplicate top-level YAML keys (silent data loss)."""
    seen_keys = {}
    for i, line in enumerate(text.split("\n"), 1):
        m = re.match(r"^([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:", line)
        if m:
            key = m.group(1)
            if key in seen_keys:
                print(f"  WARN: Duplicate key '{key}' at line {i} (first at line {seen_keys[key]}) — last value wins", file=sys.stderr)
            seen_keys[key] = i
    return text


def strip_markdown_fences(text: str) -> str:
    """Remove ```yaml ... ``` wrapping, even if embedded in surrounding text."""
    # Try to extract content between ``` fences
    m = re.search(r"```(?:ya?ml)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: strip first/last line if they are fences
    lines = text.strip().split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def remove_xml_tags(text: str) -> str:
    """Remove XML/HTML tag hallucinations from LLM output.

    Catches: </parameter>, </invoke>, <*>, </*>,
    <tool_use>, </tool_use>, <result>, </result>, etc.
    """
    # Remove full XML tags (opening and closing)
    text = re.sub(r"</?(?:antml|parameter|invoke|tool_use|result|function_calls)[^>]*>", "", text)
    # Remove any remaining XML-like tags that aren't part of YAML content
    # Be conservative: only remove tags on their own line
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are purely XML tags
        if re.match(r"^</?[a-zA-Z_][a-zA-Z0-9_:.-]*[^>]*>\s*$", stripped):
            continue
        # Remove inline XML tags
        line = re.sub(r"</?(?:antml|parameter|invoke|tool_use|result|function_calls)[^>]*>", "", line)
        cleaned.append(line)
    return "\n".join(cleaned)


def fix_yaml_preamble(text: str) -> str:
    """Remove non-YAML text before the first YAML key or '---'."""
    lines = text.split("\n")
    # Find first line that looks like YAML (key: value, ---, or list item)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("---") or stripped.startswith("$schema:") or stripped.startswith("knows_version:"):
            return "\n".join(lines[i:])
        # Any line with "key: value" pattern at indent 0
        if re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*\s*:", stripped):
            return "\n".join(lines[i:])
    return text


def fix_nested_quotes(text: str) -> str:
    """Fix YAML double-quote escaping issues.

    Common pattern: title: "Why would "money" protect me"
    Should be: title: "Why would \\"money\\" protect me"
    Or use single quotes: title: 'Why would "money" protect me'
    """
    lines = text.split("\n")
    fixed = []
    for line in lines:
        # Match lines like: key: "value with "nested" quotes"
        # Strategy: if a line has an odd number of unescaped quotes after the colon,
        # switch the outer delimiters to single quotes
        m = re.match(r"^(\s*\w[\w.]*:\s*)\"(.*)\"(\s*#.*)?$", line)
        if m:
            prefix, content, comment = m.group(1), m.group(2), m.group(3) or ""
            # Count unescaped internal quotes
            internal_quotes = len(re.findall(r'(?<!\\)"', content))
            if internal_quotes > 0:
                # Switch to single-quote wrapping, escape any single quotes in content
                content_escaped = content.replace("'", "''")
                line = f"{prefix}'{content_escaped}'{comment}"
        fixed.append(line)
    return "\n".join(fixed)


def validate_yaml(text: str) -> tuple:
    """Try to parse YAML and return (parsed_dict, error_message)."""
    try:
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data, None
        return None, f"YAML root is {type(data).__name__}, expected mapping"
    except yaml.YAMLError as e:
        return None, str(e)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Sanitize LLM-generated sidecar YAML")
    parser.add_argument("input", help="Input YAML file (or - for stdin)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--in-place", action="store_true", help="Overwrite input file")
    parser.add_argument("--quiet", action="store_true", help="Suppress diagnostic output")
    args = parser.parse_args()

    # Read input
    if args.input == "-":
        raw = sys.stdin.read()
        source = "stdin"
    else:
        p = Path(args.input)
        if not p.exists():
            print(f"ERROR: File not found: {p}", file=sys.stderr)
            sys.exit(1)
        raw = p.read_text()
        source = str(p)

    # Check if already valid
    original_data, original_error = validate_yaml(raw)
    if original_data is not None:
        if not args.quiet:
            print(f"  {source}: Already valid YAML mapping — no sanitization needed", file=sys.stderr)
        output_text = raw
    else:
        if not args.quiet:
            print(f"  {source}: Invalid YAML ({original_error})", file=sys.stderr)
            print(f"  Applying sanitization...", file=sys.stderr)

        cleaned = sanitize(raw)
        cleaned_data, cleaned_error = validate_yaml(cleaned)

        if cleaned_data is not None:
            if not args.quiet:
                print(f"  FIXED: Now valid YAML mapping", file=sys.stderr)
            output_text = cleaned
        else:
            if not args.quiet:
                print(f"  STILL INVALID after sanitization: {cleaned_error}", file=sys.stderr)
                print(f"  Writing sanitized output anyway — manual fix needed", file=sys.stderr)
            output_text = cleaned

    # Write output
    if args.in_place and args.input != "-":
        Path(args.input).write_text(output_text)
        if not args.quiet:
            print(f"  Written: {args.input}", file=sys.stderr)
    elif args.output:
        Path(args.output).write_text(output_text)
        if not args.quiet:
            print(f"  Written: {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(output_text)


if __name__ == "__main__":
    main()
