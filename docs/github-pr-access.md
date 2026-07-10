# GitHub PR access from the VPS

Este documento descreve o acesso mínimo necessário para o agente abrir branches e PRs no repositório público `icidade/miniCISO`.

## Recomendação

Prefira **Fine-grained Personal Access Token**.

### Fine-grained PAT recomendado

- **Repository access**: `Only select repositories`
- Repositório: `icidade/miniCISO`

Permissões mínimas:

- **Contents**: `Read and write`
- **Pull requests**: `Read and write`
- **Metadata**: `Read-only`

Isso basta para:

- clonar/consultar via API autenticada;
- criar branch;
- push;
- abrir PR com `gh pr create`.

> Se o PR também alterar arquivos de workflow do GitHub Actions (por exemplo `.github/workflows/*`), podem ser necessárias permissões adicionais além do mínimo acima.

### Fallback: Classic PAT

Se usar classic PAT no lugar do fine-grained:

- para repo público, o mínimo prático costuma ser `public_repo`;
- se no futuro o repo ficar privado, usar `repo`.

## Onde guardar na VPS

### Opção recomendada para o Hermes profile

Guardar fora do repo, no profile ativo:

```bash
/home/vpsadmin/.hermes/profiles/chief-of-staff/.env
```

Adicionar:

```bash
GH_TOKEN=<seu_pat>
```

Opcionalmente também:

```bash
GITHUB_TOKEN=<seu_pat>
```

Depois reiniciar a sessão/gateway que executa esse profile.

### Opção via gh CLI (persistência do cliente GitHub)

Com o token no ambiente:

```bash
gh auth login --with-token <<< "$GH_TOKEN"
gh auth setup-git
gh auth status
```

Isso grava a autenticação do `gh` fora do repo (tipicamente em `~/.config/gh/hosts.yml`) e configura integração com `git` para push por HTTPS.

## Como verificar

```bash
gh auth status
git -C /home/vpsadmin/miniCISO remote -v
git -C /home/vpsadmin/miniCISO ls-remote origin
```

Se quiser validar a API diretamente:

```bash
python3 - <<'PY'
import os, urllib.request, json
req = urllib.request.Request('https://api.github.com/user')
req.add_header('Authorization', f"token {os.environ['GH_TOKEN']}")
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.status)
    print(r.headers.get('X-OAuth-Scopes', ''))
    print(json.load(r)['login'])
PY
```

## Fluxo de PR depois da credencial pronta

```bash
cd /home/vpsadmin/miniCISO
git checkout -b chore/minha-mudanca
# editar / exportar / validar
git add -A
git commit -m "docs: update miniCISO public overlay"
git push -u origin chore/minha-mudanca
gh pr create --fill
```

## Não fazer

- não salvar o PAT dentro do repositório;
- não commitar `.env`, `hosts.yml`, ou qualquer arquivo de auth;
- não reaproveitar um token com escopo maior do que o necessário.
