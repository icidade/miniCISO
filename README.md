# miniCISO

Staff de segurança agentic para [Hermes Agent](https://github.com/NousResearch/hermes-agent), distribuído como um overlay reproduzível de perfis, prompts, templates e políticas operacionais.

> Este repositório **não é um fork do Hermes**. O runtime é instalado pelo bootstrap a partir de uma versão e um commit imutáveis declarados em [`config/hermes-version.env`](config/hermes-version.env).

## Restauração rápida

### Windows (PowerShell)

```powershell
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
.\scripts\bootstrap.ps1
```

### Linux, macOS ou WSL2

```bash
git clone https://github.com/icidade/miniCISO.git
cd miniCISO
./scripts/bootstrap.sh
```

O bootstrap:

1. baixa o instalador oficial do Hermes pelo commit fixado e valida seu SHA-256;
2. instala o runtime sem gravar segredos no repositório;
3. executa o setup local do provedor/modelo;
4. cria os nove perfis MiniCISO a partir da configuração local;
5. instala cada `SOUL.md`, cria o workspace compartilhado e configura o terminal local;
6. executa verificações estruturais.

As credenciais solicitadas por `hermes setup` ficam no ambiente Hermes do usuário. Nunca são copiadas para este repositório.

## Perfis

- `chief-of-staff`: coordenador MiniCISO e síntese final
- `security-threat-modeling`
- `security-architecture`
- `security-code-review`
- `security-appsec-assessment`
- `security-compliance-mapper`
- `security-offensive-security`
- `security-recon-attack-surface-strategist`
- `security-qa`: gate final de qualidade

O `chief-of-staff` é um perfil Hermes dedicado e gerenciado integralmente por este overlay. O bootstrap não altera o prompt do perfil Hermes padrão.

## Validação

Validação offline da árvore:

```powershell
.\scripts\validate-repo.ps1
```

```bash
./scripts/validate-repo.sh
```

Depois do bootstrap, valide o runtime:

```powershell
.\scripts\smoke-test.ps1
```

Use `-Online`/`--online` para também enviar uma pergunta curta a cada perfil. Essa modalidade consome o provedor configurado.

## Segurança e privacidade

O repo contém somente configuração não secreta e conteúdo sanitizado. Não publique `.env`, tokens, sessões, memórias, logs ou relatórios reais. Consulte [`SECURITY.md`](SECURITY.md) e [`.env.example`](.env.example).

## Documentação

- [`INSTALL.md`](INSTALL.md): instalação, atualização, rollback e limitações
- [`docs/staff-operating-model.md`](docs/staff-operating-model.md): fluxo operacional
- [`docs/profile-setup.md`](docs/profile-setup.md): contrato dos perfis
- [`docs/dependencies-and-configuration.md`](docs/dependencies-and-configuration.md): dependências opcionais
- [`miniciso-staff-service-catalog-v4-full.pdf`](miniciso-staff-service-catalog-v4-full.pdf): catálogo de serviços

## Licença

[MIT](LICENSE). O Hermes Agent é um projeto separado e mantém sua própria licença.
