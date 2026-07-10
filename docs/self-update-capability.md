# Self-update capability (public/safe overlay)

Esta capability existe para manter o repositório público `miniCISO` alinhado com a instância viva da VPS **sem copiar estado privado**.

## Objetivo

Gerar uma cópia pública e segura de:

- tools locais do Headroom/KAG que façam sentido como overlay público;
- snapshot sanitizado de configuração não secreta do perfil `chief-of-staff`;
- documentação metodológica não confidencial.

## O que entra

Atualmente o export seguro cobre:

- `tools/headroom_phase1/*.py`
- `tools/headroom_phase1/tests/test_*.py`
- `config/chief-of-staff.public.yaml`

## O que fica de fora

Nunca exportar:

- `.env`, `.env.*`, tokens, PATs, API keys
- `auth.json`, `hosts.yml`, cookies, credenciais do `gh`
- memórias, sessões, logs, cron output
- artefatos raw de assessment
- referências a programas BBP específicos em andamento
- findings, triage notes, evidência sensível

## Script de export

O export atual é **allowlisted + scanned + reviewed-by-diff**:

- só copia um conjunto fixo de arquivos públicos do Headroom/KAG;
- faz bloqueio se detectar padrões suspeitos de segredo/estado operacional;
- ainda exige revisão humana do `git diff` antes de commit/push.

Use:

```bash
python3 scripts/export_safe_self_state.py
```

Modo apply:

```bash
python3 scripts/export_safe_self_state.py --apply
```

Também é possível apontar fontes explícitas:

```bash
python3 scripts/export_safe_self_state.py \
  --source-workspace /home/vpsadmin/miniciso-security \
  --source-profile /home/vpsadmin/.hermes/profiles/chief-of-staff \
  --apply
```

## Fluxo recomendado de atualização

1. Rodar o export seguro.
2. Revisar `git diff` no repo público.
3. Rodar `./scripts/validate-repo.sh`.
4. Rodar testes dos tools públicos, quando aplicável.
5. Commitar em branch própria.
6. Abrir PR.

## Critério de inclusão

Antes de promover algo do runtime vivo para o repo público, confirmar:

- é reproduzível;
- é genericamente útil;
- não revela segredo ou contexto privado;
- não depende de um programa/engagement específico em andamento;
- ainda faz sentido fora da VPS atual.
