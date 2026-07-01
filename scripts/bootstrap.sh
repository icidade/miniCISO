#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$REPO_ROOT/config/hermes-version.env"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
WORKSPACE_ROOT="${MINICISO_WORKSPACE_ROOT:-$HOME/miniciso-security}"
SKIP_HERMES_INSTALL=false
SKIP_PROVIDER_SETUP=false

usage() {
  cat <<'EOF'
Usage: bootstrap.sh [--skip-hermes-install] [--skip-provider-setup]

Installs the pinned Hermes runtime, configures a local provider, and restores
all MiniCISO profiles. Secrets remain in the local Hermes home.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-hermes-install) SKIP_HERMES_INSTALL=true ;;
    --skip-provider-setup) SKIP_PROVIDER_SETUP=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# shellcheck disable=SC1090
source "$VERSION_FILE"
: "${HERMES_COMMIT:?missing HERMES_COMMIT}"
: "${HERMES_TAG:?missing HERMES_TAG}"
: "${HERMES_INSTALL_SH_SHA256:?missing HERMES_INSTALL_SH_SHA256}"

echo "MiniCISO: Hermes $HERMES_TAG ($HERMES_COMMIT)"

if [[ "$SKIP_HERMES_INSTALL" == false ]]; then
  installer="$(mktemp)"
  trap 'rm -f "$installer"' EXIT
  curl --fail --silent --show-error --location \
    "https://raw.githubusercontent.com/NousResearch/hermes-agent/$HERMES_COMMIT/scripts/install.sh" \
    --output "$installer"

  if command -v sha256sum >/dev/null 2>&1; then
    actual_hash="$(sha256sum "$installer" | awk '{print toupper($1)}')"
  else
    actual_hash="$(shasum -a 256 "$installer" | awk '{print toupper($1)}')"
  fi
  if [[ "$actual_hash" != "$HERMES_INSTALL_SH_SHA256" ]]; then
    echo "Invalid Hermes installer checksum: $actual_hash" >&2
    exit 1
  fi

  bash "$installer" \
    --commit "$HERMES_COMMIT" \
    --hermes-home "$HERMES_HOME" \
    --dir "$HERMES_HOME/hermes-agent" \
    --skip-setup \
    --non-interactive
fi

export PATH="$HERMES_HOME/bin:$HOME/.local/bin:$PATH"
if ! command -v hermes >/dev/null 2>&1; then
  echo 'hermes command not found. Open a new shell and rerun with --skip-hermes-install.' >&2
  exit 1
fi

if [[ "$SKIP_PROVIDER_SETUP" == false ]]; then
  echo 'Configure the local provider/model. No credentials are written to this repo.'
  hermes setup
fi

profile_root="$HOME/.hermes/profiles"
profiles=()
for profile_dir in "$REPO_ROOT"/profiles/*; do
  [[ -d "$profile_dir" ]] && profiles+=("${profile_dir##*/}")
done
if [[ ${#profiles[@]} -ne 9 ]]; then
  echo "Expected 9 profiles, found ${#profiles[@]}." >&2
  exit 1
fi

for profile in "${profiles[@]}"; do
  destination_dir="$profile_root/$profile"
  if [[ ! -d "$destination_dir" ]]; then
    echo "Creating profile $profile"
    hermes profile create "$profile" --clone
  fi
  mkdir -p "$destination_dir"
  source_soul="$REPO_ROOT/profiles/$profile/SOUL.md"
  destination_soul="$destination_dir/SOUL.md"
  if [[ -f "$destination_soul" ]] && ! cmp -s "$source_soul" "$destination_soul"; then
    cp "$destination_soul" "$destination_soul.pre-miniciso"
  fi
  cp "$source_soul" "$destination_soul"
done

mkdir -p "$WORKSPACE_ROOT"/{inputs,drafts,qa,reports,templates}
cp "$REPO_ROOT"/templates/* "$WORKSPACE_ROOT/templates/"

for profile in "${profiles[@]}"; do
  hermes -p "$profile" config set terminal.backend local
  hermes -p "$profile" config set terminal.cwd "$WORKSPACE_ROOT"
done

"$SCRIPT_DIR/validate-repo.sh"
echo
echo 'MiniCISO restored. Run scripts/smoke-test.sh to validate the runtime.'
