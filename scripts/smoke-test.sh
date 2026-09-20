#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ONLINE=false
[[ ${1:-} == '--online' ]] && ONLINE=true
[[ ${1:-} == '--hermes-home' ]] && { HERMES_HOME="$2"; shift 2; }
[[ ${1:-} == '--online' ]] && ONLINE=true

expected_repository="$(awk -F= '$1=="HERMES_REPOSITORY" {print $2}' "$REPO_ROOT/config/hermes-version.env")"
expected_commit="$(awk -F= '$1=="HERMES_COMMIT" {print $2}' "$REPO_ROOT/config/hermes-version.env")"
canonical_repo() { local value="${1%.git}"; [[ "$value" =~ ^https://github\.com/([^/]+)/([^/]+)$ ]] && printf '%s/%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" || [[ "$value" =~ ^git@github\.com:([^/]+)/([^/]+)$ ]] && printf '%s/%s' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" || return 1; }
runtime="$HERMES_HOME/hermes-agent"
[[ "$expected_repository" == 'https://github.com/icidade/hermes-agent.git' ]] || { echo 'Unexpected Hermes repository.' >&2; exit 1; }
[[ "$expected_commit" == 'a921e389f130b3a46c9f1b7363dae6ab1c87f6c5' ]] || { echo 'Unexpected Hermes commit.' >&2; exit 1; }
[[ -d "$runtime/.git" ]] || { echo 'Hermes checkout missing.' >&2; exit 1; }
[[ "$(git -C "$runtime" rev-parse HEAD)" == "$expected_commit" ]] || { echo 'Hermes HEAD mismatch.' >&2; exit 1; }
[[ "$(canonical_repo "$(git -C "$runtime" config --get remote.origin.url)")" == "$(canonical_repo "$expected_repository")" ]] || { echo 'Hermes origin mismatch.' >&2; exit 1; }
hermes="$runtime/venv/bin/hermes"
python="$runtime/venv/bin/python"
[[ -x "$hermes" && -x "$python" ]] || { echo 'Hermes executable or Python missing from checkout.' >&2; exit 1; }
"$python" - "$runtime" <<'PY'
import importlib, pathlib, sys
runtime = pathlib.Path(sys.argv[1]).resolve()
for name in ('hermes_cli', 'hermes_cli.config', 'hermes_constants'):
    if runtime not in pathlib.Path(importlib.import_module(name).__file__).resolve().parents:
        raise SystemExit('Hermes module provenance mismatch')
for path in sys.path:
    path_obj = pathlib.Path(path).resolve()
    if 'hermes-agent' in path and path_obj != runtime and runtime not in path_obj.parents:
        raise SystemExit('Hermes sys.path provenance mismatch')
PY
mapfile -t expected_profiles < <(find "$REPO_ROOT/profiles" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
mapfile -t installed_profiles < <("$hermes" profile list | awk 'NF {print $1}' | sort -u)
[[ "${expected_profiles[*]}" == "${installed_profiles[*]}" ]] || { echo 'Hermes profiles do not match exactly.' >&2; exit 1; }
for profile in "${expected_profiles[@]}"; do
  root="$HERMES_HOME/profiles/$profile"
  [[ -f "$root/SOUL.md" && -f "$root/config.yaml" ]] || { echo "Profile files missing: $profile" >&2; exit 1; }
done
chief="$HERMES_HOME/profiles/chief-of-staff"
[[ -f "$chief/skills/cost-context-governance/SKILL.md" ]] || { echo 'Governance skill missing.' >&2; exit 1; }
grep -Fq 'cost-context-governance' "$chief/SOUL.md" || { echo 'Chief SOUL missing governance reference.' >&2; exit 1; }
grep -Fq 'mode: enforce' "$chief/config.yaml" || { echo 'Chief governance mode is not enforce.' >&2; exit 1; }
if [[ "$ONLINE" == true ]]; then
  for profile in "${expected_profiles[@]}"; do "$hermes" -p "$profile" chat -Q -q 'Answer in one line starting with OK.'; done
fi
echo "Smoke test completed for ${#expected_profiles[@]} exact profiles."