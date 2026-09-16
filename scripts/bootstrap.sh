#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$REPO_ROOT/config/hermes-version.env"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
WORKSPACE_ROOT="${MINICISO_WORKSPACE_ROOT:-$HOME/miniciso-security}"
SKIP_HERMES_INSTALL=false
SKIP_PROVIDER_SETUP=false
FORCE_HERMES_REINSTALL=false

usage() {
  cat <<'EOF'
Usage: bootstrap.sh [--skip-hermes-install] [--skip-provider-setup] [--force-hermes-reinstall]

Installs Hermes from the configured repository at the exact configured SHA,
then restores the MiniCISO overlay. Secrets remain in the local Hermes home.
EOF
}

resolve_python() {
  command -v python3 2>/dev/null || command -v python 2>/dev/null || {
    echo 'python3/python not found' >&2
    return 1
  }
}

canonical_repo() {
  local value="${1%.git}"
  if [[ "$value" =~ ^https://github\.com/([^/]+)/([^/]+)$ ]]; then
    printf '%s/%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
  elif [[ "$value" =~ ^git@github\.com:([^/]+)/([^/]+)$ ]]; then
    printf '%s/%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
  else
    echo 'Unsupported Hermes repository URL.' >&2
    return 1
  fi
}

fail_provenance() {
  echo "Hermes provenance check failed: $1" >&2
  return 1
}

prepare_checkout() {
  local runtime_dir="$1"
  local expected_repo="$2"
  local expected_commit="$3"
  local expected_owner_repo
  expected_owner_repo="$(canonical_repo "$expected_repo")"

  if [[ ! -d "$runtime_dir/.git" ]]; then
    mkdir -p "$runtime_dir"
    git -C "$runtime_dir" init -q
    git -C "$runtime_dir" remote add origin "$expected_repo"
  fi
  git -C "$runtime_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail_provenance 'checkout is not a Git repository'
  local origin
  origin="$(git -C "$runtime_dir" config --get remote.origin.url || true)"
  [[ -n "$origin" ]] || fail_provenance 'origin is missing'
  [[ "$(canonical_repo "$origin")" == "$expected_owner_repo" ]] || fail_provenance 'origin does not match configured repository'
  if ! git -C "$runtime_dir" cat-file -e "$expected_commit^{commit}" 2>/dev/null; then
    git -C "$runtime_dir" fetch --no-tags --depth=1 origin "$expected_commit"
  fi
  git -C "$runtime_dir" checkout --detach "$expected_commit" >/dev/null
}

verify_provenance() {
  local runtime_dir="$1"
  local expected_repo="$2"
  local expected_commit="$3"
  local expected_owner_repo
  expected_owner_repo="$(canonical_repo "$expected_repo")"
  git -C "$runtime_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail_provenance 'checkout is not a Git repository'
  [[ "$(git -C "$runtime_dir" rev-parse HEAD)" == "$expected_commit" ]] || fail_provenance 'HEAD does not match configured commit'
  [[ "$(canonical_repo "$(git -C "$runtime_dir" config --get remote.origin.url)")" == "$expected_owner_repo" ]] || fail_provenance 'origin does not match configured repository'
  local hermes_cmd="$runtime_dir/venv/bin/hermes"
  local hermes_python="$runtime_dir/venv/bin/python"
  [[ -x "$hermes_cmd" ]] || fail_provenance 'Hermes executable is outside the governed checkout or missing'
  [[ -x "$hermes_python" ]] || fail_provenance 'Hermes Python is outside the governed checkout or missing'
  "$hermes_python" - "$runtime_dir" <<'PY'
import importlib
import pathlib
import sys

runtime = pathlib.Path(sys.argv[1]).resolve()
for name in ("hermes_cli", "hermes_cli.config", "hermes_constants"):
    module = importlib.import_module(name)
    path = pathlib.Path(module.__file__).resolve()
    if runtime not in path.parents:
        raise SystemExit(f"Hermes module outside governed checkout: {name}")
for entry in sys.path:
    entry_path = pathlib.Path(entry).resolve()
    if "hermes-agent" in entry and entry_path != runtime and runtime not in entry_path.parents:
        raise SystemExit("Hermes sys.path selects another checkout")
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-hermes-install) SKIP_HERMES_INSTALL=true ;;
    --skip-provider-setup) SKIP_PROVIDER_SETUP=true ;;
    --force-hermes-reinstall) FORCE_HERMES_REINSTALL=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# shellcheck disable=SC1090
source "$VERSION_FILE"
: "${HERMES_REPOSITORY:?missing HERMES_REPOSITORY}"
: "${HERMES_COMMIT:?missing HERMES_COMMIT}"
: "${HERMES_INSTALL_SH_SHA256:?missing HERMES_INSTALL_SH_SHA256}"

export HERMES_HOME
PYTHON_BIN="$(resolve_python)"
runtime_dir="$HERMES_HOME/hermes-agent"

if [[ "$FORCE_HERMES_REINSTALL" == true && -e "$runtime_dir" ]]; then
  rm -rf "$runtime_dir"
fi

if [[ "$SKIP_HERMES_INSTALL" == false ]]; then
  installer="$(mktemp)"
  trap 'rm -f "$installer"' EXIT
  repo_path="${HERMES_REPOSITORY%.git}"
  [[ "$repo_path" =~ ^https://github\.com/([^/]+)/([^/]+)$ ]] || { echo 'Unsupported Hermes repository URL.' >&2; exit 1; }
  raw_base="https://raw.githubusercontent.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  curl --fail --silent --show-error --location "$raw_base/$HERMES_COMMIT/scripts/install.sh" --output "$installer"
  actual_hash="$(sha256sum "$installer" | awk '{print toupper($1)}')"
  [[ "$actual_hash" == "$HERMES_INSTALL_SH_SHA256" ]] || { echo 'Invalid Hermes installer checksum.' >&2; exit 1; }
  prepare_checkout "$runtime_dir" "$HERMES_REPOSITORY" "$HERMES_COMMIT"
  bash "$installer" --commit "$HERMES_COMMIT" --force-commit --hermes-home "$HERMES_HOME" --dir "$runtime_dir" --skip-setup --non-interactive
fi

# This is deliberately before any profile, skill, config, or template write.
verify_provenance "$runtime_dir" "$HERMES_REPOSITORY" "$HERMES_COMMIT"
hermes_cmd="$runtime_dir/venv/bin/hermes"

if [[ "$SKIP_PROVIDER_SETUP" == false ]]; then
  echo 'Configure the local provider/model. No credentials are written to this repo.'
  "$hermes_cmd" setup
fi

profile_root="$HERMES_HOME/profiles"
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
    "$hermes_cmd" profile create "$profile" --clone
  fi
  mkdir -p "$destination_dir"
  source_soul="$REPO_ROOT/profiles/$profile/SOUL.md"
  destination_soul="$destination_dir/SOUL.md"
  if [[ -f "$destination_soul" ]] && ! cmp -s "$source_soul" "$destination_soul"; then
    cp "$destination_soul" "$destination_soul.pre-miniciso"
  fi
  cp "$source_soul" "$destination_soul"
done

skills_source="$REPO_ROOT/skills"
chief_skills_root="$profile_root/chief-of-staff/skills"
mkdir -p "$chief_skills_root"
while IFS= read -r -d '' skill_file; do
  rel_path="${skill_file#"$skills_source/"}"
  destination_skill="$chief_skills_root/$rel_path"
  mkdir -p "$(dirname "$destination_skill")"
  cp "$skill_file" "$destination_skill"
done < <(find "$skills_source" -type f -print0)

"$PYTHON_BIN" "$SCRIPT_DIR/install_governance_config.py" \
  --source "$REPO_ROOT/config/chief-of-staff.public.yaml" \
  --profile-config "$profile_root/chief-of-staff/config.yaml"

mkdir -p "$WORKSPACE_ROOT"/{inputs,drafts,qa,reports,templates}
cp "$REPO_ROOT"/templates/* "$WORKSPACE_ROOT/templates/"
for profile in "${profiles[@]}"; do
  "$hermes_cmd" -p "$profile" config set terminal.backend local
  "$hermes_cmd" -p "$profile" config set terminal.cwd "$WORKSPACE_ROOT"
done

"$SCRIPT_DIR/validate-repo.sh"
echo 'MiniCISO restored. Run scripts/smoke-test.sh to validate the runtime.'