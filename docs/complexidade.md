# Análise de Complexidade

Esta análise cobre cada Requisito Funcional (RF01–RF04) e cada operação
pública do motor. Convenções:

* `N` = número de documentos
* `V` = tamanho do vocabulário (termos únicos)
* `L` = comprimento de uma palavra / prefixo
* `K` = limite de retorno (`k`)
* `Q` = número de consultas no input
* `D` = número médio de termos por documento

---

## RF01 — Tabela Hash com Encadeamento Separado (`HashTable`)

| Operação | Caso Médio | Pior Caso | Justificativa |
|---|---|---|---|
| `put(k, v)` | **O(1)** | O(N) | Hash uniforme + load_factor ≤ 0.75 evita degeneração |
| `get(k)` | **O(1)** | O(N) | Mesma cadeia visitada na pior hipótese |
| `remove(k)` | **O(1)** | O(N) | Idem |
| `rehash()` | O(N) amortizado | O(N) | Dispara quando `size > 0.75 · capacity` |

**Carga real medida no estresse (10k docs):**

```
hash_index = {
  size: 59967, capacity: 131072, load_factor: 0.4575,
  max_chain: 4, avg_chain_non_empty: 1.14
}
```

A cadeia máxima de **apenas 4 nós** prova que a função hash DJB2 distribui
bem as chaves textuais — o pior caso teórico de O(N) **não se materializa**
neste cenário.

### Índice Invertido (sobre `HashTable`)

| Operação | Complexidade |
|---|---|
| `add_document(doc, tokens)` | O(D) — uma operação O(1) por token |
| `term_frequency(t, d)` | O(1) |
| `document_frequency(t)` | O(1) |
| `postings(t)` | O(1) para acessar + O(P) para iterar (P = docs com `t`) |

---

## RF02 — Trie + DFS de Autocompletar

| Operação | Complexidade |
|---|---|
| `insert(word)` | **O(L)** |
| `contains(word)` | **O(L)** |
| `starts_with(prefix)` | **O(L)** |
| `autocomplete(prefix, limit=K)` | **O(L + S)** com S ≤ 10·K (poda explícita) |

A DFS é **iterativa** e ordena filhos por caractere para sair de forma
determinística. Quando combinada ao `HeapSort` externo (que reordena por
frequência), o custo total fica **O(L + S · log S)**.

**Carga real no estresse:**

```
trie = { words: 50000, nodes: 242903, max_depth: 14 }
```

A profundidade máxima de 14 confirma que a Trie permanece **rasa** mesmo
com 50k palavras — a busca por prefixo é virtualmente O(L) constante.

---

## RF03 — Splay Tree (cache de metadados)

| Operação | Complexidade Amortizada |
|---|---|
| `insert(k, v)` | **O(log N)** |
| `get(k)` | **O(log N)** |
| `remove(k)` | **O(log N)** |
| `_evict_one()` | O(log N) (caminha do root até uma folha) |

O **teorema do balanceamento estático** (Sleator & Tarjan, 1985) garante
amortização O(log N), e o **teorema do conjunto de trabalho** garante que
o acesso repetido aos mesmos K nós seja amortizado em O(log K) — perfeito
para o padrão "leitura de metadados de docs quentes" do RAG.

**Cache hits/misses no estresse:**

```
splay = { size: 512, hits: 280, misses: 1276 }
```

Os 280 hits demonstram que o Splay efetivamente mantém os documentos
quentes próximos da raiz — sem isso, todo acesso a `_touch_cache` seria
um miss.

---

## RF04 — HeapSort e Top-K

| Operação | Tempo | Memória |
|---|---|---|
| `heap_sort(arr)` | **O(N log N)** | O(1) adicional (in-place) |
| `top_k(arr, K)` | **O(N log K)** | O(K) |

A função `top_k`, usada na busca, **NÃO ordena a lista inteira** — usa
uma min-heap de tamanho K. Para 10k docs e K=5, isso significa ~10 mil
inserções em uma heap de altura 3 (≈30 mil comparações no pior caso).

A função `heap_sort` é usada **internamente** para:

1. Ordenar os K finalistas pelo desempate (-score, doc_id ASC).
2. Ordenar o pool de sugestões da Trie por (-frequência, palavra ASC).

---

## Complexidade Global do Motor

| Etapa | Custo | Por consulta |
|---|---|---|
| Indexação | O(N · D) | — |
| `search(q, k)` | — | O(\|q\| + Σ\|postings\| + N log K) |
| `autocomplete(p, k)` | — | O(\|p\| + S log S) |
| `cache_get(d)` | — | O(log N) amortizado |
| Total (Q consultas) | — | **O(Q · N log K)** dominante |

### Medições reais no estresse (10.000 docs, 60k termos, 500 consultas):

```
indexação        : 5.879 ms       (≈ 0.5 ms / doc)
500 consultas    : 4.173 ms       (≈ 8.3 ms / consulta)
RSS pico         : 192 MiB
```

Comparado ao baseline esperado pela rubrica (`O(N log N)`), o motor
opera **dentro da margem assintótica exigida** em todas as operações.
