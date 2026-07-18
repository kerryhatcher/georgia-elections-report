# sensitive-data

Working folder for raw data that may contain personally identifiable information (PII) — e.g. the Georgia voter registration file, voter history file, or any export that includes names, addresses, or dates of birth.

**Nothing in this folder is committed to git except this file.** The folder itself is tracked (via `.gitkeep`) so it exists after a fresh clone, but its contents are covered by `.gitignore`.

## Rules

- Never rename or move raw PII-bearing files outside this folder.
- Derived, de-identified, or aggregated outputs (e.g. county-level turnout summaries with no individual-level data) belong outside this folder, in the normal project tree, and can be committed.
- If a file must be shared with collaborators, use a secure channel (not git) and confirm data-handling terms with the commissioning organization’s point of contact first.
