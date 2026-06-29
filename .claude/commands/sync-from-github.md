---
description: Safely pull latest changes from GitHub with conflict diagnostics
---

Safely pull the latest changes from the GitHub remote.

Steps:
1. Run `git remote -v` — if no remote, stop and tell the user
2. Run `git status` — if there are uncommitted changes, warn the user and ask whether to stash them first
3. Run `git fetch origin` to preview what's incoming
4. Run `git log HEAD..origin/main --oneline` to show incoming commits
5. If clean, run `git pull origin main`
6. If there are merge conflicts, report them clearly and do NOT auto-resolve — ask the user how to proceed

Note: GitHub remote is not yet initialized as of 2026-06-29.
