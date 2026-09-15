#!/usr/bin/env python3
"""
Unified code search wrapper. Routes to ripgrep or ast-grep based on query type.
Enriches Python results with the function/class that contains each match.

Routing rules:
  - func_name()  or  func_name($$$)  →  ast-grep  (finds calls, not the definition)
  - @decorator                        →  ast-grep  (decorator search)
  - ast:<pattern>                     →  ast-grep  (explicit)
  - everything else                   →  ripgrep   (text / regex)

All ripgrep flags (e.g. -i, -C, --glob) are passed through transparently.
"""
import subprocess, sys, json, re, io

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Python symbol enrichment
# ---------------------------------------------------------------------------

def find_python_symbol(file_path, line_no):
    """Return 'function foo' or 'class Bar' that contains line_no."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return None

    pattern = re.compile(r'^(\s*)(def|async\s+def|class)\s+([A-Za-z_][A-Za-z0-9_]*)')
    stack = []
    current = None

    for i, raw in enumerate(lines, start=1):
        m = pattern.match(raw)
        if m:
            indent = len(m.group(1).replace('\t', '    '))
            kind = 'function' if 'def' in m.group(2) else 'class'
            name = m.group(3)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            stack.append((indent, kind, name))
        if i > line_no:
            break
        if stack:
            current = stack[-1]

    return f"{current[1]} {current[2]}" if current else None


def print_match(path, line_no, text, skip_symbol=False):
    """Print a match in grep format, with Python symbol context appended."""
    print(f"{path}:{line_no}:{text.rstrip()}")
    if not skip_symbol and str(path).endswith(".py"):
        symbol = find_python_symbol(path, line_no)
        if symbol:
            print(f"  ├─ {symbol}")


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def detect_query_type(raw_query):
    """Return (engine, query) where engine is 'ast' or 'rg'."""
    if raw_query.startswith("ast:"):
        return "ast", raw_query[4:]

    if raw_query.startswith("text:"):
        return "rg", raw_query[5:]

    # Decorator pattern: @something
    if raw_query.startswith("@"):
        return "ast", raw_query

    # Function call pattern: name() or name($$$) or name($_)
    if re.match(r'^[A-Za-z_]\w*\(', raw_query):
        # Normalise bare name() → name($$$) for ast-grep
        if raw_query.endswith("()"):
            return "ast", raw_query[:-2] + "($$$)"
        return "ast", raw_query

    return "rg", raw_query


# ---------------------------------------------------------------------------
# ripgrep runner
# ---------------------------------------------------------------------------

def run_ripgrep(query, extra_args):
    """Run ripgrep and enrich Python matches with symbol context."""
    cmd = ["rg", "--json", "-n", query] + extra_args

    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError:
        print("Error: ripgrep (rg) not found. Install with: choco install ripgrep", file=sys.stderr)
        return 1

    for raw in p.stdout:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except Exception:
            continue

        kind = obj.get("type")
        if kind == "match":
            data = obj["data"]
            path    = data.get("path", {}).get("text", "")
            line_no = data.get("line_number")
            text    = data.get("lines", {}).get("text", "")
            print_match(path, line_no, text)
        elif kind == "context":
            # Print context lines (from -C / -A / -B flags) without symbol enrichment
            data = obj["data"]
            path    = data.get("path", {}).get("text", "")
            line_no = data.get("line_number")
            text    = data.get("lines", {}).get("text", "").rstrip()
            print(f"{path}-{line_no}-{text}")

    p.stdout.close()
    stderr_data = p.stderr.read()
    p.stderr.close()
    p.wait()

    # If ripgrep failed (bad regex, etc), print error
    if p.returncode != 0:
        if stderr_data and "parse error" in stderr_data.lower():
            print(f"Invalid regex pattern: {stderr_data.strip()}", file=sys.stderr)
        return p.returncode

    return p.returncode


# ---------------------------------------------------------------------------
# ast-grep runner
# ---------------------------------------------------------------------------

def run_astgrep(pattern, extra_args):
    """Run ast-grep for structural matching, enrich Python matches."""
    cmd = ["ast-grep", "--pattern", pattern, "--lang", "python", "--json"]

    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError:
        print("ast-grep not found — falling back to ripgrep.", file=sys.stderr)
        return run_ripgrep(pattern, extra_args)

    stdout_data = p.stdout.read()
    stderr_data = p.stderr.read()
    p.stdout.close()
    p.stderr.close()
    p.wait()

    # If ast-grep failed (non-zero exit or stderr), fall back to ripgrep
    if p.returncode != 0:
        if stderr_data:
            print(f"ast-grep error: {stderr_data.strip()} — falling back to ripgrep.", file=sys.stderr)
        return run_ripgrep(pattern, extra_args)

    try:
        results = json.loads(stdout_data)
    except Exception:
        print("ast-grep returned invalid JSON — falling back to ripgrep.", file=sys.stderr)
        return run_ripgrep(pattern, extra_args)

    if not results:
        # No matches — fall back so ripgrep can try as plain text
        return run_ripgrep(pattern, extra_args)

    # Detect if this is a decorator search (pattern starts with @)
    is_decorator_search = pattern.startswith("@")

    for item in results:
        path    = item.get("file", "")
        line_no = item.get("range", {}).get("start", {}).get("line", 0) + 1  # 0-indexed
        # "lines" is the full source line; "text" is only the matched node
        text    = item.get("lines", item.get("text", ""))
        # For multi-line matches keep only the first line
        first_line = text.split("\n")[0]
        # Skip symbol context for decorators
        print_match(path, line_no, first_line, skip_symbol=is_decorator_search)

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python search.py <query> [ripgrep_flags...]", file=sys.stderr)
        print("  query examples:", file=sys.stderr)
        print("    get_exact_vals()      — function calls (ast-grep)", file=sys.stderr)
        print("    @router.get($$$)      — decorator (ast-grep)", file=sys.stderr)
        print("    filters_map           — text search (ripgrep)", file=sys.stderr)
        print("    ast:<pattern>         — force ast-grep", file=sys.stderr)
        print("    text:<pattern>        — force ripgrep", file=sys.stderr)
        sys.exit(1)

    raw_query  = sys.argv[1]
    extra_args = sys.argv[2:]       # ripgrep flags like -i, -C 2, --glob "*.py"

    engine, query = detect_query_type(raw_query)

    if engine == "ast":
        exit_code = run_astgrep(query, extra_args)
    else:
        exit_code = run_ripgrep(query, extra_args)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
