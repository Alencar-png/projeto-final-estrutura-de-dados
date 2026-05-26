# Motor RAG Local — Projeto Final de Estrutura de Dados

> **Projeto 1** — Motor de busca textual offline para uma IA que não pode
> acessar a internet. Indexação invertida, autocompletar via Trie, cache
> adaptativo via Splay e ranking Top-K via HeapSort.

[![tests](https://img.shields.io/badge/tests-18%2F18-brightgreen)](#testes)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](#requisitos)
[![status](https://img.shields.io/badge/status-pronto%20para%20entrega-success)](#)

---

## 1. Autoria

**Trabalho individual.**

| Nome | Responsabilidade |
|---|---|
| **Guilherme Romualdo** | Projeto integral — RF01 a RF04, gerador de dados, documentação e testes |

---

## 2. Projeto Escolhido

**Projeto 1 — Motor RAG (Retrieval-Augmented Generation) Local**

| RF | Estrutura | Local |
|---|---|---|
| RF01 | Tabela Hash com encadeamento separado | [`src/structures/hash_table.py`](src/structures/hash_table.py) |
| RF01 | Índice Invertido construído sobre a Hash | [`src/structures/inverted_index.py`](src/structures/inverted_index.py) |
| RF02 | Árvore Trie + DFS iterativa de autocompletar | [`src/structures/trie.py`](src/structures/trie.py) |
| RF03 | Árvore Splay (cache de metadados quentes) | [`src/structures/splay_tree.py`](src/structures/splay_tree.py) |
| RF04 | HeapSort + Top-K (min-heap de tamanho K) | [`src/structures/heap_sort.py`](src/structures/heap_sort.py) |

---

## 3. Estrutura do Repositório

```
projeto-final-estrutura-de-dados/
├── README.md                 ← este arquivo
├── Makefile                  ← alvos make install / gen-all / run-* / verify-* / stress
├── run.sh                    ← execução padrão (input -> output)
├── requirements.txt          ← apenas Faker (para GERAÇÃO de dados)
├── src/
│   ├── main.py               ← CLI principal (lê input.json, escreve output.json)
│   ├── structures/           ← RF01..RF04, todas implementadas do ZERO
│   │   ├── hash_table.py
│   │   ├── inverted_index.py
│   │   ├── trie.py
│   │   ├── splay_tree.py
│   │   └── heap_sort.py
│   ├── engine/
│   │   ├── tokenizer.py      ← normalização Unicode (NFD) + lowercase
│   │   └── rag_engine.py     ← orquestrador (search / autocomplete / cache)
│   ├── generators/
│   │   └── generate_data.py  ← gera input_{basico,avancado,estresse}.json
│   └── tools/
│       ├── diff_outputs.py   ← compara saída real x gabarito
│       └── stress_bench.py   ← mede tempo + pico de RAM
├── data/
│   ├── input_basico.json     ← cenário pequeno (5 docs, 7 consultas)
│   ├── input_avancado.json   ← edge cases (vazios, duplicatas, cache miss)
│   ├── input_estresse.json   ← 10.000 docs, 60k termos, 500 consultas (6.5 MiB)
│   ├── output_esperado_basico.json
│   ├── output_esperado_avancado.json
│   └── output_esperado_estresse.json
├── docs/
│   ├── arquitetura.md
│   ├── complexidade.md
│   ├── prova_de_carga.md
│   └── relatorio/
│       ├── gerar_relatorio.py     ← script que monta o DOCX
│       ├── Relatorio_Motor_RAG.docx
│       └── Relatorio_Motor_RAG.pdf  ← relatório acadêmico final (ABNT, A4, 13 pp)
└── tests/
    └── test_structures.py    ← 18 testes unitários
```

---

## 4. Requisitos

* Python **3.10+**
* Apenas para geração de dados sintéticos: `Faker==25.0.0`

> O **núcleo algorítmico não importa nenhuma biblioteca externa**. Apenas
> `src/generators/generate_data.py` usa `Faker`, conforme explicitamente
> permitido pela rubrica.

---

## 5. Como Executar

### Setup inicial

```bash
make install            # instala Faker (opcional, só p/ gerar massa)
```

### Gerar os três cenários de teste

```bash
make gen-basico
make gen-avancado
make gen-estresse
# ou tudo de uma vez:
make gen-all
```

### Rodar o motor em cada cenário

```bash
make run-basico         # data/input_basico.json   -> data/output_real_basico.json
make run-avancado       # data/input_avancado.json -> data/output_real_avancado.json
make run-estresse       # data/input_estresse.json -> data/output_real_estresse.json
```

Ou diretamente:

```bash
./run.sh data/input_basico.json data/output_real_basico.json
```

### Validar saída contra o gabarito

```bash
make verify-basico      # diff entre esperado e real
make verify-avancado
```

Saída esperada: `[OK] Saídas coincidem (N resultados).`

### Prova de carga

```bash
make stress
```

### Relatório acadêmico (ABNT)

```bash
make relatorio       # gera docs/relatorio/Relatorio_Motor_RAG.docx
make relatorio-pdf   # converte para PDF (requer LibreOffice/soffice instalado)
```

O relatório final em formato ABNT (Times New Roman 12pt, espaçamento 1,5,
margens 3-3-2-2, página A4) está versionado em
[`docs/relatorio/Relatorio_Motor_RAG.pdf`](docs/relatorio/Relatorio_Motor_RAG.pdf).

Saída esperada (varia por hardware):

```
documentos indexados : 10000
termos únicos        : 59967
total de consultas   : 500
tempo de indexação   : ~5800 ms
tempo de consultas   : ~4200 ms
pico de memória RSS  : ~192 MiB
```

---

## 6. Formato dos Arquivos

### `input.json`

```json
{
  "documentos": [
    {
      "id": "doc1",
      "titulo": "Título do documento",
      "conteudo": "Texto que será tokenizado e indexado.",
      "metadados": {"autor": "...", "ano": 2024}
    }
  ],
  "consultas": [
    {"tipo": "search",       "query": "termos da busca", "k": 5},
    {"tipo": "autocomplete", "prefix": "pa",             "limit": 10},
    {"tipo": "cache_get",    "doc_id": "doc1"}
  ]
}
```

### `output.json`

```json
{
  "resultados": [
    {
      "id": 0,
      "tipo": "search",
      "query": "termos da busca",
      "k": 5,
      "top_k": [
        {"doc_id": "doc1", "score": 0.853, "titulo": "..."}
      ]
    },
    {
      "id": 1,
      "tipo": "autocomplete",
      "prefix": "pa",
      "limit": 10,
      "sugestoes": ["palavra", "passos"]
    },
    {
      "id": 2,
      "tipo": "cache_get",
      "doc_id": "doc1",
      "metadados": {"id": "doc1", "titulo": "...", "metadados": {...}}
    }
  ],
  "estatisticas": {
    "indice_invertido": { ... },
    "trie": { ... },
    "cache_splay": { ... },
    "tempo_indexacao_ms": 5879.3,
    "tempo_consultas_ms": 4173.1,
    "total_consultas": 500
  }
}
```

O campo `estatisticas` reporta métricas de carga (tempo e cache hits/misses).
A ferramenta `diff_outputs` ignora esse campo, comparando estritamente
`resultados`.

---

## 7. Atendimento aos Requisitos Funcionais

| RF | Descrição | Implementação |
|---|---|---|
| **RF01** | Índice invertido em memória mapeando palavras → IDs de docs | `InvertedIndex` sobre `HashTable` própria; expõe `term_frequency`, `document_frequency`, `postings`, `doc_length` |
| **RF02** | Autocompletar via caminhamento DFS na Trie | `Trie.autocomplete_with_frequency` percorre a sub-árvore com DFS iterativa; resultado final é reordenado por **HeapSort** |
| **RF03** | Cache de metadados dos documentos mais acessados | `SplayTree` com `capacity`; cada `cache_get` realiza um splay levando o doc para a raiz; evict político da folha mais fria |
| **RF04** | Top-5 por relevância | `top_k` usa min-heap de tamanho K (O(N log K)); empates desempatados por `doc_id` ASC para garantir determinismo |

---

## 8. Garantias de Qualidade

### 8.1 Anti-Hardcode

* O gabarito de **TODOS** os cenários (incluindo estresse) é gerado pela
  **mesma implementação** que será auditada.
* Não há `if/else` para casos especiais: a saída sempre passa pelo motor real.

### 8.2 Determinismo

* `HashTable` usa função DJB2 própria — não depende de `PYTHONHASHSEED`.
* `Trie.autocomplete` ordena filhos por caractere antes da DFS.
* `RAGEngine.search` ordena os Top-K por `(-score, doc_id ASC)` no final.
* Gerador de dados usa `random.Random(seed=42)` reprodutível.

### 8.3 Testes

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

* **18 testes** cobrem `HashTable`, `Trie`, `SplayTree`, `HeapSort`,
  `top_k` e `InvertedIndex`.
* Inclui teste **fuzz** com 2.000 operações aleatórias na `HashTable`.

### 8.4 Limites Assintóticos (resumo)

| Operação | Complexidade |
|---|---|
| `HashTable.put/get/remove` | **O(1)** amortizado |
| `Trie.autocomplete(p, K)` | **O(\|p\| + S log S)** com poda `S = 10·K` |
| `SplayTree.get/insert/remove` | **O(log N)** amortizado |
| `heap_sort` | **O(N log N)** |
| `top_k` | **O(N log K)** |

Análise completa em [`docs/complexidade.md`](docs/complexidade.md).

---

## 9. Prova de Carga (cenário de estresse)

> Meta exigida: **10.000 documentos**, **50.000 palavras únicas**.

| Métrica | Exigido | Obtido |
|---|---|---|
| Documentos | ≥ 10.000 | **10.000** |
| Palavras únicas | ≥ 50.000 | **59.967** (+19%) |
| Tempo de indexação | suportar carga | **~5.9 s** |
| Tempo de 500 consultas | suportar carga | **~4.2 s** (~8 ms/query) |
| Pico de RAM | sem estouro | **~192 MiB** |
| Determinismo | exato | 500/500 resultados idênticos entre execuções |

Detalhes em [`docs/prova_de_carga.md`](docs/prova_de_carga.md).

---

## 10. Bibliotecas Permitidas vs. Proibidas

| Componente | Lib permitida? | Justificativa |
|---|---|---|
| `Faker` em `src/generators/generate_data.py` | Sim | Geração de dados falsos (rubrica permite explicitamente) |
| `random` no gerador | Sim | Massa de testes |
| `json` (stdlib) | Sim | Serialização de input/output |
| `unicodedata` (stdlib) | Sim | Normalização Unicode (NFD) — não substitui nenhuma estrutura central |
| `math.log` no scoring TF-IDF | Sim | Função matemática primitiva |
| `bisect` no gerador | Sim | Amostragem ponderada do **gerador**, não do núcleo |
| `dict`, `set`, `list` do Python no núcleo | **Não** (no núcleo) | Substituídos por `HashTable` própria. As únicas `list` no núcleo são buffers internos das estruturas (e.g. arrays de buckets), nunca como Tabela Hash de propósito geral. |
| Bibliotecas como `numpy`, `pandas`, `networkx`, `sortedcontainers` | **Proibidas** | Não estão importadas em nenhum arquivo do núcleo |

---

## 11. Roteiro de Auditoria (para o Code Review)

Reproduza esses passos para auditar o projeto do zero:

```bash
# 1. Clonar repositório
git clone <url>; cd projeto-final-estrutura-de-dados

# 2. Instalar dependência de geração de dados (opcional)
make install

# 3. Rodar testes unitários
PYTHONPATH=. python3 -m unittest discover -s tests -v

# 4. Reproduzir as 3 massas (substitui os arquivos em /data)
make gen-all

# 5. Rodar os 3 cenários
make run-basico
make run-avancado
make run-estresse

# 6. Confirmar determinismo contra os gabaritos
make verify-basico
make verify-avancado

# 7. Confirmar limites de tempo e memória
make stress
```

---

## 12. Licença

Uso acadêmico — Universidade.
