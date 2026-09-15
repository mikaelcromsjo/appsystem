# Claude Search Wrapper

Windows-ready wrapper around `rg` that limits hits/files and returns a short message when the search is too broad.

## Defaults

The wrapper is tuned so Claude can usually run a short command only:

- `--mode compact`
- `--max-hits 12`
- `--max-files 6`
- `--root .`

These are a good default balance: enough signal to be useful, but small enough to avoid bloating context.

## What it does

- Stops after `--max-files` files and `--max-hits` hits.
- If the search is too broad in `compact` mode, returns only:
  - `Found many matches (X+ hits across Y+ files). Refine the search before reading files.`
- For Python files, tries to add the enclosing function/class name.
- Removes noisy ripgrep JSON from the final output.

## Requirements

- Python 3.10+
- `rg` installed and on PATH
- Optional: `ast-grep` installed for future extension

## Usage

### Short default command

```powershell
python .\search_wrapper.py "fooBar"
```

### Narrow to Python files

```powershell
python .\search_wrapper.py "fooBar" --glob "*.py"
```

### Narrow to a folder

```powershell
python .\search_wrapper.py "fooBar" --glob "src/auth/**"
```

### Override limits

```powershell
python .\search_wrapper.py "fooBar" --max-hits 20 --max-files 10
```

## Example fake queries

- `fooBar`
- `processThing`
- `handleEvent`
- `token refresh`
- `UserService`

## Suggested Claude prompt

Use this tool first. If it says the search is too broad, refine the query before reading files.
