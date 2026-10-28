#!/usr/bin/env bash
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
NEW="$ROOT/scripts/new_worktree.sh"
CLEAN="$ROOT/scripts/cleanup_worktree.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

# Isolated fixture repository with an initial commit and copies of the scripts.
fixture="$tmp/repo"
mkdir -p "$fixture/scripts"
cp "$NEW" "$CLEAN" "$fixture/scripts/"
chmod +x "$fixture/scripts/new_worktree.sh" "$fixture/scripts/cleanup_worktree.sh"
git -C "$fixture" init -q
git -C "$fixture" config user.name "Worktree Test"
git -C "$fixture" config user.email "worktree-test@example.invalid"
printf 'fixture\n' > "$fixture/README.md"
git -C "$fixture" add README.md
git -C "$fixture" commit -qm "initial commit"

cd "$fixture"
./scripts/new_worktree.sh backend STORY-1 >/dev/null || fail "creation should succeed"
[[ -d ../worktrees/wt-backend-STORY-1 ]] || fail "expected worktree directory"
[[ "$(git -C ../worktrees/wt-backend-STORY-1 branch --show-current)" == "feat/STORY-1-backend" ]] || fail "wrong branch"
pass "creation uses expected path and branch"

if ./scripts/new_worktree.sh backend STORY-1 >/dev/null 2>&1; then fail "duplicate worktree should fail"; fi
pass "duplicate creation fails"

if ./scripts/new_worktree.sh "" STORY-2 >/dev/null 2>&1; then fail "empty agent should fail"; fi
if ./scripts/new_worktree.sh backend "" >/dev/null 2>&1; then fail "empty story should fail"; fi
pass "empty arguments fail"

if ./scripts/cleanup_worktree.sh backend MISSING >/dev/null 2>&1; then fail "missing worktree cleanup should fail"; fi
pass "cleanup of missing worktree fails"

if printf 'no\n' | ./scripts/cleanup_worktree.sh backend STORY-1 >/dev/null 2>&1; then fail "cleanup should require explicit yes"; fi
[[ -d ../worktrees/wt-backend-STORY-1 ]] || fail "cancelled cleanup removed worktree"
pass "cleanup requests confirmation and preserves worktree when declined"

if printf 'yes\n' | ./scripts/cleanup_worktree.sh backend STORY-1 >/dev/null 2>&1; then :; else fail "confirmed cleanup should succeed"; fi
[[ ! -e ../worktrees/wt-backend-STORY-1 ]] || fail "confirmed cleanup left worktree"
pass "confirmed cleanup removes the worktree"

if ./scripts/cleanup_worktree.sh main STORY-1 >/dev/null 2>&1; then fail "cleanup must refuse main"; fi
pass "cleanup refuses main"

./scripts/new_worktree.sh backend STORY-3 >/dev/null || fail "creation should succeed"
git -C ../worktrees/wt-backend-STORY-3 switch -q -c someone-elses-branch
if printf 'yes\n' | ./scripts/cleanup_worktree.sh backend STORY-3 >/dev/null 2>&1; then fail "cleanup removed a worktree on another branch"; fi
[[ -d ../worktrees/wt-backend-STORY-3 ]] || fail "branch-mismatch cleanup removed the worktree"
pass "cleanup refuses a worktree on an unexpected branch"

echo "All worktree tests passed."
