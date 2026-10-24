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
  echo "Error: agent and story must be simple slugs." >&2
  exit 1
}

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Error: run this script inside a Git repository." >&2
  exit 1
}
cd "$repo_root"
worktree="../worktrees/wt-$agent-$story"

# Guard both the requested identity and the resolved Git worktree metadata.
if [[ "$agent" == "main" || "$story" == "main" || "$worktree" == "." || "$worktree" == "$repo_root" ]]; then
  echo "Error: refusing to remove main or the repository root." >&2
  exit 1
fi
if [[ ! -e "$worktree" ]]; then
  echo "Error: worktree does not exist: $worktree" >&2
  exit 1
fi

worktree_root=$(git -C "$worktree" rev-parse --show-toplevel 2>/dev/null) || {
  echo "Error: target is not a valid Git worktree: $worktree" >&2
  exit 1
}
worktree_branch=$(git -C "$worktree" branch --show-current)
if [[ "$worktree_root" == "$repo_root" || "$worktree_branch" == "main" ]]; then
  echo "Error: refusing to remove main or the primary repository checkout." >&2
  exit 1
fi

printf 'Remove worktree %s (branch %s)? This does not delete the branch. Type yes to confirm: ' "$worktree" "$worktree_branch"
IFS= read -r confirmation
if [[ "$confirmation" != "yes" ]]; then
  echo "Cancelled; worktree preserved."
  exit 1
fi

git worktree remove "$worktree"
printf 'Removed worktree: %s\n' "$worktree"
