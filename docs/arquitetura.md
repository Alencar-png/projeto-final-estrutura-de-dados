# Arquitetura do Motor RAG Local

## Visão Geral

O sistema é um **motor de busca textual offline** que indexa documentos JSON
e responde a três tipos de consultas:

1. `search`       → top-K documentos por relevância TF-IDF
2. `autocomplete` → completar prefixo a partir do vocabulário indexado
3. `cache_get`    → recuperar metadados de um documento (com cache adaptativo)

Toda a I/O é feita por linha de comando, lendo um único arquivo `input.json`
e escrevendo um único arquivo `output.json`. A saída é **determinística**
para uma mesma entrada — propriedade verificada via `src/tools/diff_outputs.py`.

## Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────────┐
│                         src/main.py (CLI)                        │
│         parse args → load input → engine.run → write output      │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                src/engine/rag_engine.py (Orquestrador)           │
│  ingest_documents  / search  / autocomplete  / cache_get         │
└──────┬───────────┬──────────────────┬───────────────────┬────────┘
       │           │                  │                   │
       │           │                  │                   │
       ▼           ▼                  ▼                   ▼
   Tokenizer   InvertedIndex        Trie             SplayTree
  (NFD + lower)  (RF01 — Hash)   (RF02 — DFS)   (RF03 — cache LRU-like)
                     │                                    │
                     └──────► HashTable (RF01) ◄──────────┘
                                       │
                                       ▼
                            HeapSort / top_k (RF04)
```

## Fluxo de uma consulta `search`

1. `tokenize(query)` normaliza acentos (NFD) e quebra em termos.
2. Para cada termo, busca a posting list no **HashTable** (RF01).
3. Acumula score TF-IDF por documento numa **HashTable** auxiliar:

   ```
   score(d) = Σ_{t ∈ q} tf(t,d) · idf(t)
   idf(t)   = log((1+N) / (1+df(t))) + 1
   tf(t,d)  = count(t,d) / max(1, |d|)
   ```

4. **`top_k`** (RF04) extrai os K maiores em **O(N · log K)** com uma
   min-heap de tamanho K — nunca paga O(N log N).
5. Empates de score são desempatados por `doc_id` ascendente (determinismo).
6. Para cada doc retornado, `_touch_cache(doc_id)` insere o documento na
   **Splay Tree** (RF03), trazendo-o para a raiz.

## Decisões de Projeto

| Decisão | Justificativa |
|---|---|
| **DJB2 como hash padrão** | Boa distribuição em chaves textuais; determinismo independente de `PYTHONHASHSEED`. |
| **Encadeamento separado** | Mais simples de implementar e raciocinar do que open-addressing; degradação graceful em colisões. |
| **Trie usando HashTable própria nos filhos** | Mantém o "do zero" mesmo na representação de filhos da Trie (sem usar `dict` no núcleo). |
| **DFS iterativa** | Evita estouro de pilha em prefixos profundos. |
| **Splay com `capacity`** | Modela cache LRU-like: eviction sempre na folha mais profunda do lado oposto ao topo (frio). |
| **Top-K com min-heap de tamanho K** | O(N log K) é estritamente melhor que ordenar tudo (O(N log N)). |
| **TF-IDF clássico** | Não exige dependência externa, é determinístico e mostra uso real do índice invertido. |
| **Desempate por `doc_id`** | Garante saída determinística (rubrica exige saída exata). |
| **Normalização NFD** | Permite buscar "arvore" e casar com "árvore" (padrão em sistemas de busca). |

## Bibliotecas Externas

O **núcleo algorítmico** não importa nada além da stdlib do Python.
Apenas o módulo `src/generators/generate_data.py` usa `Faker` para criar
títulos sintéticos — uso explicitamente permitido pela rubrica
("É permitido o uso de bibliotecas auxiliares exclusivamente para geração
de dados falsos e serialização JSON").
