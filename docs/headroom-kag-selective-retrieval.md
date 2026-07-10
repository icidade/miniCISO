# Headroom + KAG selective retrieval

Este documento descreve a camada pública e sanitizada da evolução do Headroom para **selection-first** guiado por hipótese/KAG.

## Motivação

Quando um artefato estruturado domina o custo de contexto, a próxima evolução não é comprimir melhor o arquivo inteiro. É:

```text
hipótese -> seleção estrutural -> retrieval pack mínimo -> compressão opcional -> raciocínio -> expansão ao raw quando necessário
```

Isso substitui o fluxo menos preciso:

```text
artefato inteiro -> compressão -> raciocínio
```

## Contrato operacional

Regra obrigatória:

- **ausência no retrieval pack nunca é evidência de ausência no artefato bruto**;
- se a evidência exigida não apareceu no pack, o estado correto é **`not_verified_in_raw`**;
- claims finais continuam dependentes do raw-authoritative review.

## Componentes públicos desta fase

Os componentes versionados em `tools/headroom_phase1/` são:

- `hr_index_artifact.py`: índice estrutural local com `json_path`, `parent_path`, `ancestors`, `signals`, `estimated_tokens` e hash da fonte;
- `hr_kag_query.py`: schema de query orientado por hipótese/superfície;
- `hr_selective_retrieval.py`: seleção determinística com orçamento (`token_budget`) e razões de inclusão;
- `hr_manual_wrapper.py`: wrapper de execução/log, agora apto a registrar metadata de `selection_first` em shadow mode.

## Shadow mode

A recomendação inicial é operar em **shadow mode**:

1. gerar índice estrutural;
2. gerar query KAG;
3. produzir retrieval pack;
4. continuar executando o fluxo raw/full em paralelo;
5. comparar economia, evidência recuperada e `decision_delta`.

## Proveniência mínima do pack

Cada slice selecionado deve preservar, no mínimo:

- `json_path`
- `parent_path` ou contexto equivalente
- `ancestors`
- `reason_selected`
- `source_sha256` ou versão/hash equivalente

## Métricas úteis

Além de economia de tokens, acompanhar:

- `source_tokens_estimated`
- `selected_tokens_estimated`
- `selection_saved_tokens`
- `selection_ratio`
- `raw_expansion_rate`
- `retrieval_precision`
- `retrieval_recall`
- `false_omission_events`
- `decision_delta`

## Escopo público deste repo

Este repo pode carregar:

- código dos seletores/indexadores/wrapper;
- testes unitários dos componentes;
- configuração pública/sanitizada do overlay;
- documentação metodológica.

Este repo **não** deve carregar:

- artefatos brutos reais de assessment;
- logs operacionais com contexto sensível;
- referências a programas BBP específicos em andamento;
- findings, reproduções ou trilhas de triage não sanitizadas.
