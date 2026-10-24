#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <agent> <story>" >&2
  exit 1
}

[[ $# -eq 2 ]] || usage
agent=${1}
story=${2}
[[ -n "$agent" && -n "$story" ]] || usage
slug_re='^[A-Za-z0-9][A-Za-z0-9._-]*$'
[[ "$agent" =~ $slug_re && "$story" =~ $slug_re ]] || {
  echo "Error: agent and story must be simple slugs (letters, digits, dot, underscore, hyphen)." >&2
  exit 1
}
[[ "$agent" != "main" && "$story" != "main" ]] || {
  echo "Error: 'main' is not a valid agent/story slug for worktree creation." >&2
  exit 1
}

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Error: run this script inside a Git repository." >&2
  exit 1
}
cd "$repo_root"
worktree="../worktrees/wt-$agent-$story"
branch="feat/$story-$agent"

if [[ -e "$worktree" ]]; then
  echo "Error: worktree path already exists: $worktree" >&2
  exit 1
fi
if git show-ref --verify --quiet "refs/heads/$branch"; then
  echo "Error: branch already exists: $branch" >&2
  exit 1
fi

mkdir -p "$(dirname "$worktree")"
git worktree add "$worktree" -b "$branch" HEAD
printf 'Created worktree: %s\nBranch: %s\n' "$worktree" "$branch"
