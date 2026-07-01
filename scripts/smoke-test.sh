#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
ONLINE=false
[[ ${1:-} == '--online' ]] && ONLINE=true

command -v hermes >/dev/null 2>&1 || { echo 'hermes command not found' >&2; exit 1; }
profile_list="$(hermes profile list)"
profiles=()
for profile_dir in "$REPO_ROOT"/profiles/*; do
  [[ -d "$profile_dir" ]] && profiles+=("${profile_dir##*/}")
done

for profile in "${profiles[@]}"; do
  grep -Fq "$profile" <<<"$profile_list" || { echo "Profile not registered: $profile" >&2; exit 1; }
  [[ -f "$HOME/.hermes/profiles/$profile/SOUL.md" ]] || { echo "SOUL.md not installed: $profile" >&2; exit 1; }
  echo "OK: $profile"
  if [[ "$ONLINE" == true ]]; then
    hermes -p "$profile" chat -Q -q 'Responda em uma linha começando com OK e informe seu papel no MiniCISO.'
  fi
done

echo "Smoke test completed for ${#profiles[@]} profiles."
