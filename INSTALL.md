# Instalação e restauração

## Pré-requisitos

- Git
- acesso HTTPS ao GitHub e aos endpoints usados pelo instalador oficial do Hermes
- uma credencial válida para ao menos um provedor/modelo suportado pelo Hermes

Python, `uv`, Node.js e as demais dependências do runtime são administrados pelo instalador oficial fixado pelo projeto.

## Instalação limpa

Windows:

```powershell
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
.\scripts\bootstrap.ps1
```

Linux, macOS ou WSL2:

```bash
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
./scripts/bootstrap.sh
```

O setup do provedor é interativo porque as credenciais não pertencem ao Git. Para preparar somente arquivos/perfis em um ambiente já configurado, use `-SkipProviderSetup` no PowerShell ou `--skip-provider-setup` no Bash.

## O que é reproduzível

- upstream, tag e commit do Hermes
- checksum dos instaladores upstream
- nomes e prompts dos perfis
- estrutura do workspace
- backend e diretório de trabalho do terminal
- testes estruturais e smoke tests

Credenciais, tokens, sessões, memórias e relatórios são estado local deliberadamente não reproduzido pelo repositório.

## Atualização do overlay

```bash
git pull --ff-only
./scripts/bootstrap.sh --skip-hermes-install --skip-provider-setup
```

No Windows:

```powershell
git pull --ff-only
.\scripts\bootstrap.ps1 -SkipHermesInstall -SkipProviderSetup
```

O bootstrap cria uma cópia `.pre-miniciso` antes de substituir um `SOUL.md` diferente já existente.

## Atualização do Hermes

Não use uma branch flutuante. Atualize `config/hermes-version.env` com uma release oficial, seu commit resolvido e os hashes dos dois instaladores. Depois execute as validações e teste uma restauração limpa.

## Rollback

1. faça checkout de um commit anterior deste repo;
2. execute novamente o bootstrap;
3. restaure um eventual `SOUL.md.pre-miniciso` apenas se quiser abandonar o prompt gerenciado pelo overlay.

## Verificação

```powershell
.\scripts\validate-repo.ps1
.\scripts\smoke-test.ps1
```

```bash
./scripts/validate-repo.sh
./scripts/smoke-test.sh
```

O smoke test online é opcional e exige credenciais: `.\scripts\smoke-test.ps1 -Online` ou `./scripts/smoke-test.sh --online`.

## Limitações

- O catálogo PDF é um artefato documental e não participa da execução.
- Ferramentas externas listadas em `config/tooling-dependencies.example.yaml` são opcionais.
- O backend local dá aos perfis acesso ao host; use Docker/SSH/Singularity se seu modelo de ameaça exigir isolamento.
