# Prova de Carga — Cenário de Estresse

## Meta da Rubrica (Projeto 1 — Motor RAG)

> Gerar input_estresse.json contendo no mínimo **50.000 palavras únicas**
> distribuídas em **10.000 documentos simulados**.

## Resultados Obtidos

| Métrica | Exigido | Obtido | Status |
|---|---|---|---|
| Documentos | ≥ 10.000 | 10.000 | OK |
| Palavras únicas | ≥ 50.000 | 59.967 | OK (+19%) |
| Determinismo da saída | exato | 500/500 consultas idênticas em reexecuções | OK |
| Tempo total de processo | "suportar carga massiva" | ~10 s | OK |
| Pico de RSS | "sem estouro de memória" | 192 MiB | OK |

## Como Reproduzir

```bash
# 1. Instalar dependências auxiliares (apenas Faker)
make install

# 2. Gerar o input_estresse.json
make gen-estresse

# 3. Rodar benchmark (mede tempo + pico de RAM)
make stress
```

Saída esperada:

```
[stress] lendo data/input_estresse.json (6.42 MiB)
[stress] JSON carregado em ~12 ms
[stress] -------- resultados --------
  documentos indexados : 10000
  termos únicos        : 59967
  total de consultas   : 500
  tempo de indexação   : ~5800 ms
  tempo de consultas   : ~4200 ms
  pico de memória RSS  : ~192 MiB
  hash load_factor     : 0.4575
  trie nodes           : 242903
  splay size           : 512
```

## Distribuição dos Dados

| Característica | Valor |
|---|---|
| Vocabulário base | 50.000 palavras únicas geradas combinatoriamente |
| Vocabulário final medido | ~60.000 (alguns títulos sintéticos do Faker adicionam termos) |
| Documentos | 10.000 |
| Palavras por documento | 30–80 (uniforme) |
| Distribuição de frequência | Zipf com expoente 0.9 |
| Consultas | 500 (60% search, 25% autocomplete, 15% cache_get) |

## Anti-Hardcode

O gabarito **NÃO é hardcoded**:

* `data/output_esperado_estresse.json` é gerado pela **mesma implementação**
  que será avaliada.
* Reexecutar `python -m src.main --input data/input_estresse.json --output X`
  produz um arquivo cujo campo `resultados` é idêntico ao gabarito
  (validado por `src/tools/diff_outputs.py`).
* O campo `estatisticas` contém apenas medições de tempo (varia por hardware)
  e é explicitamente **ignorado** pela ferramenta de diff.

## Garantia de Cobertura do Vocabulário

O gerador de estresse executa uma "passada de cobertura" no início, em que
as primeiras 50.000 posições de tokens consumidas pelos documentos são
preenchidas sequencialmente com o vocabulário base. Assim, **toda palavra
única aparece em pelo menos um documento**, evitando termos órfãos que
inflariam falsamente o tamanho do vocabulário.
