# Agent Worktree Isolation

## Policy

- One agent that writes code or repository files gets one dedicated Git worktree per story: `../worktrees/wt-<agent>-<story>`.
- The orchestrator creates the worktree before delegating any writing task, using `./scripts/new_worktree.sh <agent> <story>`. Pass the exact worktree path and branch to the agent.
- A writing agent may modify files only inside its assigned worktree and only within its allowed paths. It must not write into another agent's worktree or the shared checkout.
- Agents must never write directly to `main`, switch the assigned worktree to `main`, or push to `main`. All changes go through a feature branch and pull request; the human owner performs final merges.
- Do not run simultaneous writing tasks in one worktree. Parallel work is allowed only with separate worktrees and non-conflicting ownership; integration is performed by the orchestrator after work completes.
- At the end of a story, the orchestrator confirms the changes are committed or safely preserved, then runs `./scripts/cleanup_worktree.sh <agent> <story>`. Cleanup requires an explicit `yes` confirmation. Do not remove a worktree with uncommitted work unless the owner has explicitly authorized discarding it.

## Prerequisites and portability

Requires Git with worktree support (Git 2.5+), Bash, and standard POSIX utilities. The scripts target Linux, macOS, and WSL. Run them from the repository root in a Bash-compatible shell. Git must have an initial commit and the repository must be clean enough for the intended branch operation. The parent directory `../worktrees` is created as needed.

Use simple slug arguments containing letters, digits, dots, underscores, or hyphens; each must start with a letter or digit. The resulting branch is `feat/<story>-<agent>`.

## Recovery

If creation or cleanup fails, stop and report the command, exit code, and safe diagnostic output. Never work around a failure by writing to the shared checkout or `main`. Check `git worktree list` before retrying.
