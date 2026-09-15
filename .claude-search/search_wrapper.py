#!/usr/bin/env python3
"""
Drop-in replacement for grep that uses ripgrep internally and enhances output
with Python symbol context (function/class names). Accepts all ripgrep flags.
"""
import subprocess, sys, json, re


def find_python_symbol(file_path, line_no):
    """Find the function or class that contains a line number in a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return None

    current = None
    pattern = re.compile(r'^(\s*)(def|async\s+def|class)\s+([A-Za-z_][A-Za-z0-9_]*)')
    stack = []

    for i, raw in enumerate(lines, start=1):
        m = pattern.match(raw)
        if m:
            indent = len(m.group(1).replace('\t', '    '))
            kind = 'function' if 'def' in m.group(2) else 'class'
            name = m.group(3)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            stack.append((indent, kind, name, i))
        if i > line_no:
            break
        if stack:
            current = stack[-1]

    if current:
        return f"{current[1]} {current[2]}"
    return None


def main():
    # Pass all arguments to ripgrep, preserve original args
    cmd = ["rg", "--json", "-n"] + sys.argv[1:]

    try:
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
    except FileNotFoundError:
        print("Error: ripgrep not found. Install with: choco install ripgrep", file=sys.stderr)
        sys.exit(1)

    for line in p.stdout:
        line = line.strip()
        if not line:
            continue

        try:
            obj = json.loads(line)
        except Exception:
            continue

        if obj.get("type") != "match":
            continue

        data = obj.get("data", {})
        path = data.get("path", {}).get("text", "")
        line_no = data.get("line_number")
        text = data.get("lines", {}).get("text", "").rstrip("\n")

        # Output in grep format: file:line:text
        output = f"{path}:{line_no}:{text}"
        print(output)

        # Add Python symbol context on next line if available and different file
        if str(path).endswith(".py"):
            symbol = find_python_symbol(path, line_no)
            if symbol:
                print(f"  ├─ {symbol}")

    p.stdout.close()
    p.wait()
    sys.exit(p.returncode)


if __name__ == "__main__":
    main()
