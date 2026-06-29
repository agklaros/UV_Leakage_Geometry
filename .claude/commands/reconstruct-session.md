---
description: Rebuild HANDOFF.md from git history after a crash or lost context
---

Reconstruct the current session state and write it to UV_Leakage_Geometry/HANDOFF.md after a crash or lost context.

To reconstruct:
1. Run `git log --oneline -20` to see recent commits
2. Run `git diff HEAD~1` to see what changed in the last commit
3. Run `git status` to see any uncommitted changes
4. Check modification times of key files (notebooks, scripts, data/matched/)
5. Read UV_Leakage_Geometry/HANDOFF.md to see the last known state

Then write a new HANDOFF entry marked "[RECONSTRUCTED]" summarizing what can be inferred about what happened, what the current state is, and what was likely being worked on.
