# Repo Mapping

This repository is the canonical public MiniCISO overlay. It is consumed directly; it is not copied into a Hermes fork.

## Source-to-runtime mapping

```text
profiles/<profile>/SOUL.md
  -> ~/.hermes/profiles/<profile>/SOUL.md

templates/*
  -> ~/miniciso-security/templates/*

config/hermes-version.env
  -> input imutável para o instalador oficial do Hermes
```

Os diretórios `inputs`, `drafts`, `qa`, `reports` e `templates` são criados em `~/miniciso-security` (ou no caminho configurado no bootstrap).

## Chief of staff

`chief-of-staff` é um perfil nomeado dedicado, não o perfil padrão do Hermes. Por isso seu `SOUL.md` completo é gerenciado pelo overlay. O snippet em `chief-of-staff/` permanece apenas como referência para quem preferir uma integração manual.
