#About

This is system web app with a CRM application

# System

- **Backend:** FastAPI  
- **Templates:** Jinja2 + [HTMX](https://htmx.org/) + [Alpine.js](https://alpinejs.dev/)  
- **Styling:** [TailwindCSS](https://tailwindcss.com/) via CDN  

## Functionality

- Customer and Product management
- Call Center workflow
- Alarm reminder system 


## CLAUDE.md

## Documentation Location

Always write all documentation in a super compact minimal way optimized for AI. 

Documentation is under `docs/`. Each file has its own doc file (<filename>.<ext>.md). Each directory has it own documentation in UPPERCASE about all content. 'templates/TEMPLATES.md'

See `docs/DOCS.md` for the documentation index.

## DOC
Each larger edit to a file. Update the FUNCTION.md in the same directory as the function lives in. Then update the DIRECTORY.md. 

# Claude Code

## Edit files
Use unique, short search strings in prompts for precise replacements.

## Sub agents

Always use sub agents for small jobs that do not need full context.

# Python rules

Python: Wrap f-string in parentheses for implicit concatenation.

## Comments and docs

- Delete or update outdated comments; remove dead code.

## Clean code for AI

- Prefer **explicit, readable** code over clever tricks.  
