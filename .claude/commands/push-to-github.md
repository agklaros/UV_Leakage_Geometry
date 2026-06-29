---
description: Stage, commit, and push all changes to GitHub remote
---

Stage, commit, and push all current changes to GitHub.

Steps:
1. Run `git remote -v` — if no remote is set, stop and tell the user to run `git remote add origin <url>` first
2. Run `git status` to show what will be staged
3. Ask the user to confirm the commit message or provide one
4. Stage files selectively (avoid .env, credentials, large binaries)
5. Commit with the provided message
6. Push to origin main

Note: GitHub remote is not yet initialized as of 2026-06-29. This command will fail until `git remote add origin` is run.
