#!/usr/bin/env bash
set -euo pipefail

MODE="dry-run"
REAL_HOME="$(getent passwd "$(id -un)" | cut -d: -f6 2>/dev/null || true)"
if [[ -z "$REAL_HOME" ]]; then
  REAL_HOME="$HOME"
fi
TARGET_ROOT="${MINICISO_HERMES_ROOT:-$REAL_HOME/.hermes}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--apply] [--target-root PATH]

Default mode is dry-run.

Examples:
  $(basename "$0")
  $(basename "$0") --apply
  $(basename "$0") --apply --target-root /srv/hermes-root
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      MODE="apply"
      shift
      ;;
    --target-root)
      TARGET_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

copy_file() {
  local src="$1"
  local dst="$2"
  echo "[$MODE] $src -> $dst"
  if [[ "$MODE" == "apply" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
  fi
}

copy_profile_souls() {
  local profiles_src="$REPO_ROOT/profiles"
  for soul in "$profiles_src"/*/SOUL.md; do
    local profile
    profile="$(basename "$(dirname "$soul")")"
    copy_file "$soul" "$TARGET_ROOT/profiles/$profile/SOUL.md"
  done
}

copy_docs_bundle() {
  copy_file "$REPO_ROOT/chief-of-staff/SOUL-miniciso-snippet.md" "$TARGET_ROOT/docs/miniciso/chief-of-staff/SOUL-miniciso-snippet.md"
  copy_file "$REPO_ROOT/docs/staff-operating-model.md" "$TARGET_ROOT/docs/miniciso/staff-operating-model.md"
  copy_file "$REPO_ROOT/docs/profile-setup.md" "$TARGET_ROOT/docs/miniciso/profile-setup.md"
  copy_file "$REPO_ROOT/docs/repo-architecture.md" "$TARGET_ROOT/docs/miniciso/repo-architecture.md"
  copy_file "$REPO_ROOT/docs/repo-mapping.md" "$TARGET_ROOT/docs/miniciso/repo-mapping.md"
  copy_file "$REPO_ROOT/docs/dependencies-and-configuration.md" "$TARGET_ROOT/docs/miniciso/dependencies-and-configuration.md"
  copy_file "$REPO_ROOT/templates/intake-template.md" "$TARGET_ROOT/docs/miniciso/templates/intake-template.md"
  copy_file "$REPO_ROOT/templates/report-template.md" "$TARGET_ROOT/docs/miniciso/templates/report-template.md"
  copy_file "$REPO_ROOT/config/tooling-dependencies.example.yaml" "$TARGET_ROOT/docs/miniciso/config/tooling-dependencies.example.yaml"
}

echo "Mode: $MODE"
echo "Target Hermes root: $TARGET_ROOT"
copy_docs_bundle
copy_profile_souls

echo "Done."
if [[ "$MODE" == "dry-run" ]]; then
  echo "No files were written. Re-run with --apply to perform the sync."
fi
