# Runtime and dev environment

Verified against the running app, 2026-10.

## Container

- Container `appsystem`, port 8070, public at https://system.ia-ai.se.
  `backend/` is bind-mounted; uvicorn runs with `--reload`.
- **Only `*.py` changes restart the app.** A restart re-runs startup: schema create,
  admin init, CMS seed, demo seed.
- Templates are re-read when the file changes (no restart). Static files are served
  straight from disk.
- Translations are the exception — see "Translations" in [UI.md](UI.md).
- Run Python inside the container (`docker exec -i appsystem python - <<'PY'`; `-i`
  is needed for stdin). On the host there is only `python3`, without the app's
  dependencies.

## Databases

SQLite files in the Docker volume at `/dbdata`: `master.db` (logins, tenants,
global CMS default), `app.db` (tenant `default`), `<slug>.db` per extra tenant.
Datetimes are stored as naive UTC.

## Scripted requests

- The session cookie is `https_only`: a scripted login against
  `http://localhost:8070` silently loses the session. Use the https URL.
- Login: `POST /login` with form fields `email`, `password` → 303, then keep the
  cookie jar. Demo logins: `docs/TEST_DATA.md`.
- Routes that use `render()` return the whole tab shell unless the request has the
  header `HX-Request: true`. Send it to get the fragment.
- Upsert endpoints take JSON (htmx `json-enc`), not form data.

## Git

Run git as `devuser` (`runuser -u devuser -- git …`); as root it fails with
"dubious ownership" (or pass `-c safe.directory='*'` for read-only commands).

Rendering a page can modify tracked files: `backend/core/lang/lang_sv.json`
(unknown labels are appended) and `backend/pdfs/invoice_<id>.pdf` (rewritten on
every PDF request). Check `git status` before committing.

## Tooling that is missing

- `.claude-search/search.py` needs ripgrep and ast-grep; neither is installed on
  the host or in the container (`/usr/bin/sg` is the unrelated shadow-utils tool).
  Use `grep -rn` until they are installed.
- `npx tailwindcss` fails with permission denied; call the CLI through node
  (command in [UI.md](UI.md)).
