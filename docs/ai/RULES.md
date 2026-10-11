# Working rules

## Before coding

- Find the closest existing code and follow it (`verticals/companies/` for a list
  vertical, `verticals/admin/` for admin sub-pages). Do not copy from the legacy
  files listed in [ARCHITECTURE.md](ARCHITECTURE.md).
- Build only what was asked. Prefer editing over new files.

## Code

- Imports from the real module, not the shims (`models.models`,
  `core.functions.helpers`).
- Timezone-aware `datetime.now(timezone.utc)`; store naive UTC.
- Every user-visible string in a template goes through `| t`, in English.
- No Alembic migration; see "Schema policy" in ARCHITECTURE.md.
- Check access in the route itself. Hiding a button or tab is not protection.
- Remove dead code and outdated comments you touch.

## After a change

- New Tailwind class → rebuild the CSS. New label → add the Swedish value and
  restart. Both in [UI.md](UI.md).
- Verify against the running app over https with a demo login
  ([RUNTIME.md](RUNTIME.md)); a 200 from `/login` proves nothing about a tab.
- `git status`: revert incidental changes to `lang_sv.json` and `backend/pdfs/`
  that are not part of the task.

## Debugging

- An error right after an edit is almost always in that edit; re-read it first.
- Error text is often misleading (a template crash can surface as "Unexpected
  server response" or a JSON 404). Look at what changed and at
  `docker logs appsystem`.
- Checking the same files twice without a new finding means the hypothesis is
  wrong; stop and ask.

## Docs

- Write down only what cannot be read from the code and would cost time to
  rediscover: contracts between files, silent failure modes, environment quirks.
- Do not document file lists, route tables, columns, env defaults or markup — they
  go stale; point to the file instead.
- State facts as verified against the running app, with the month.
- New doc → add a row to [INDEX.md](INDEX.md). Per-file notes (`<file>.py.md`)
  only for genuinely non-obvious modules.
- When a change makes a statement here untrue, fix the statement in the same change.
