# GitHub PR access from the VPS

This document describes the minimum access needed for the agent to open branches and PRs in the public `icidade/miniCISO` repository.

## Recommendation

Prefer a **fine-grained personal access token**.

### Recommended fine-grained PAT

- **Repository access**: `Only select repositories`
- Repository: `icidade/miniCISO`

Minimum permissions:

- **Contents**: `Read and write`
- **Pull requests**: `Read and write`
- **Metadata**: `Read-only`

That is enough to:

- clone or query through the authenticated API;
- create a branch;
- push;
- open a PR via `gh pr create` or the GitHub API.

> If the PR also changes GitHub Actions workflow files (for example `.github/workflows/*`), additional permissions beyond this minimum may be required.

### Fallback: classic PAT

If you use a classic PAT instead of a fine-grained one:

- for a public repo, the practical minimum is usually `public_repo`;
- if the repo becomes private in the future, use `repo`.

## Where to store it on the VPS

### Recommended option for the Hermes profile

Store it outside the repo, in the active profile:

```bash
/home/vpsadmin/.hermes/profiles/chief-of-staff/.env
```

Add:

```bash
GITHUB_TOKEN=<your_pat>
```

Then restart the session/gateway that runs this profile.

### Optional `gh` CLI flow

If `gh` is installed and the token is already in the environment:

```bash
gh auth login --with-token <<< "$GITHUB_TOKEN"
gh auth setup-git
gh auth status
```

This stores `gh` authentication outside the repo (typically in `~/.config/gh/hosts.yml`) and configures Git integration for HTTPS push.

## How to verify

If `gh` is installed:

```bash
gh auth status
```

Always valid:

```bash
git -C /home/vpsadmin/miniCISO remote -v
git -C /home/vpsadmin/miniCISO ls-remote origin
```

To validate the API directly:

```bash
python3 - <<'PY'
import os, urllib.request, json
req = urllib.request.Request('https://api.github.com/user')
req.add_header('Authorization', f"token {os.environ['GITHUB_TOKEN']}")
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.status)
    print(r.headers.get('X-OAuth-Scopes', ''))
    print(json.load(r)['login'])
PY
```

## PR flow after the credential is ready

### With `gh`

```bash
cd /home/vpsadmin/miniCISO
git checkout -b chore/my-change
# edit / export / validate
git add -A
git commit -m "docs: update miniCISO public overlay"
git push -u origin chore/my-change
gh pr create --fill
```

### Without `gh`

Use `git push` plus the GitHub API with `GITHUB_TOKEN`.

## Do not

- do not store the PAT inside the repository;
- do not commit `.env`, `hosts.yml`, or any auth file;
- do not reuse a token with broader scope than necessary.
