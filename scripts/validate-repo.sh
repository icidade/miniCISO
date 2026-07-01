#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
errors=0

fail() {
  echo "ERROR: $*" >&2
  errors=$((errors + 1))
}

required_files=(
  README.md INSTALL.md LICENSE SECURITY.md .env.example
  config/hermes-version.env config/tooling-dependencies.example.yaml
  scripts/bootstrap.ps1 scripts/bootstrap.sh
  scripts/smoke-test.ps1 scripts/smoke-test.sh
  scripts/validate-repo.ps1 scripts/validate-repo.sh
  meta/MANIFEST.json meta/SUMMARY.json
)
for file in "${required_files[@]}"; do
  [[ -f "$REPO_ROOT/$file" ]] || fail "required file missing: $file"
done

profiles=()
for profile_dir in "$REPO_ROOT"/profiles/*; do
  [[ -d "$profile_dir" ]] && profiles+=("${profile_dir##*/}")
done
[[ ${#profiles[@]} -eq 9 ]] || fail "expected 9 profile directories; found ${#profiles[@]}"
for profile in "${profiles[@]}"; do
  [[ -s "$REPO_ROOT/profiles/$profile/SOUL.md" ]] || fail "missing or empty SOUL.md: $profile"
done

version_file="$REPO_ROOT/config/hermes-version.env"
grep -Eq '^HERMES_TAG=v[0-9]{4}\.[0-9]{1,2}\.[0-9]{1,2}$' "$version_file" || fail 'invalid HERMES_TAG'
grep -Eq '^HERMES_COMMIT=[0-9a-f]{40}$' "$version_file" || fail 'invalid HERMES_COMMIT'
[[ $(grep -Ec '^HERMES_INSTALL_(PS1|SH)_SHA256=[A-F0-9]{64}$' "$version_file") -eq 2 ]] || fail 'invalid installer checksums'

while IFS= read -r -d '' file; do
  if grep -Eq -- '-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}' "$file"; then
    fail "possible secret found: ${file#"$REPO_ROOT/"}"
  fi
done < <(find "$REPO_ROOT" -path "$REPO_ROOT/.git" -prune -o -type f \
  \( -name '*.md' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.sh' -o -name '*.ps1' -o -name '*.env' -o -name '*.example' \) -print0)

json_command=()
if python3 -c 'import json' >/dev/null 2>&1; then
  json_command=(python3 -m json.tool)
elif python -c 'import json' >/dev/null 2>&1; then
  json_command=(python -m json.tool)
fi

if [[ ${#json_command[@]} -gt 0 ]]; then
  "${json_command[@]}" "$REPO_ROOT/meta/MANIFEST.json" >/dev/null || fail 'invalid meta/MANIFEST.json'
  "${json_command[@]}" "$REPO_ROOT/meta/SUMMARY.json" >/dev/null || fail 'invalid meta/SUMMARY.json'
else
  echo 'WARN: Python unavailable; JSON syntax validation skipped.' >&2
fi

if [[ $errors -ne 0 ]]; then
  echo "Validation failed with $errors error(s)." >&2
  exit 1
fi

echo "OK: valid structure, ${#profiles[@]} profiles, and basic secret checks."
