#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
BARE="$TMP/remote.git"
WORK="$TMP/work"
mkdir "$WORK"
git init --bare "$BARE" >/dev/null
git -C "$WORK" init >/dev/null
git -C "$WORK" config user.name "Claim Test"
git -C "$WORK" config user.email "claim-test@example.invalid"
git -C "$WORK" remote add origin "$BARE"
export GIT_AUTHOR_NAME="Claim Test"
export GIT_AUTHOR_EMAIL="claim-test@example.invalid"
export GIT_COMMITTER_NAME="Claim Test"
export GIT_COMMITTER_EMAIL="claim-test@example.invalid"
export PYTHONDONTWRITEBYTECODE=1
CLAIM=(python3 "$ROOT/scripts/claim_task.py" --remote "$BARE")
RELEASE=(python3 "$ROOT/scripts/release_claim.py" --remote "$BARE")

# Two genuinely concurrent contenders: exactly one wins.
set +e
(cd "$WORK" && "${CLAIM[@]}" --task-id T-RACE --run-id run-A >"$TMP/a.out" 2>"$TMP/a.err") &
P1=$!
(cd "$WORK" && "${CLAIM[@]}" --task-id T-RACE --run-id run-B >"$TMP/b.out" 2>"$TMP/b.err") &
P2=$!
wait "$P1"; A=$?
wait "$P2"; B=$?
set -e
if ! { [[ "$A" -eq 0 && "$B" -eq 1 ]] || [[ "$A" -eq 1 && "$B" -eq 0 ]]; }; then
  echo "Expected concurrent exit codes {0,1}; got $A,$B" >&2
  cat "$TMP/a.out" "$TMP/a.err" "$TMP/b.out" "$TMP/b.err" >&2
  exit 1
fi

# Release then re-claim.
(cd "$WORK" && "${RELEASE[@]}" --task-id T-RACE)
(cd "$WORK" && "${CLAIM[@]}" --task-id T-RACE --run-id run-after-release)

# Listing must include the active claim.
LIST="$(cd "$WORK" && python3 "$ROOT/scripts/list_claims.py" --remote "$BARE")"
grep -q 'T-RACE: run_id=run-after-release' <<<"$LIST"

# Dry run prints the intended ref update and must not create a remote ref.
(cd "$WORK" && "${CLAIM[@]}" --task-id T-DRY --run-id dry-run --dry-run | grep -q 'DRY RUN: git push')
if git --git-dir="$BARE" show-ref --verify --quiet refs/claims/T-DRY; then
  echo "--dry-run unexpectedly pushed a claim" >&2
  exit 1
fi

echo "Atomic Git claim integration tests passed."
