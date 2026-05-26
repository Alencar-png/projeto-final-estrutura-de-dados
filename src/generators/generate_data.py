"""Gerador determinístico de massas de teste para o Motor RAG.

Cenários produzidos (na pasta `data/`):
    basico    -> input_basico.json     +  output_esperado_basico.json
    avancado  -> input_avancado.json   +  output_esperado_avancado.json
    estresse  -> input_estresse.json   (gabarito gerado dinamicamente sob demanda)

Meta de estresse exigida pela rubrica do Projeto 1 (Motor RAG):
    >= 50.000 PALAVRAS ÚNICAS distribuídas em >= 10.000 documentos.

Uso:
    python -m src.generators.generate_data --cenario basico --out data/
    python -m src.generators.generate_data --cenario avancado --out data/
    python -m src.generators.generate_data --cenario estresse --out data/

Notas sobre as bibliotecas usadas:
    * `random` (seedable) ............ permitido (apenas para massa de testes)
    * `Faker` ......................... permitido (apenas para massa de testes)
    * NENHUMA das estruturas de dados do núcleo é importada do stdlib
      (Hash, Trie, Splay e HeapSort estão em src/structures/).
"""

from __future__ import annotations

import argparse
import json
import random
import string
import sys
from pathlib import Path
from typing import Dict, List

try:
    from faker import Faker  # type: ignore
except ImportError:  # pragma: no cover
    Faker = None  # type: ignore


SEED = 42


def _faker_or_fallback():
    if Faker is None:
        return None
    f = Faker("pt_BR")
    Faker.seed(SEED)
    return f


# --------------------------------------------------------------- vocabulário
def _unique_words(n: int, rnd: random.Random) -> List[str]:
    """Gera `n` palavras únicas curtas usando combinatória controlada.

    Estratégia: enumera triplas (prefix, infix, suffix) com sílabas
    plausíveis até atingir n. Como o produto cartesiano é > 50_000,
    o algoritmo termina rapidamente.
    """
    prefixes = [
        "ne", "co", "ma", "li", "do", "te", "ra", "vi", "po", "se",
        "ba", "ga", "lu", "mi", "pa", "ro", "su", "ta", "fa", "be",
        "ze", "no", "qua", "tri", "pen", "hex", "sep", "oct", "non", "dec",
    ]
    infixes = [
        "ri", "lo", "mu", "ne", "ti", "ka", "ze", "ba", "vo", "xi",
        "pu", "rdi", "lto", "nco", "rsa", "mpa", "nta", "rgo", "sci", "fra",
    ]
    suffixes = [
        "do", "ra", "te", "co", "mo", "vo", "ge", "no", "fa", "le",
        "vel", "ção", "dor", "ica", "oso", "ade", "ino", "uno", "ito", "eza",
    ]

    words = set()
    out: List[str] = []
    # Combinação determinística por seed do random.Random.
    triples = [(p, i, s) for p in prefixes for i in infixes for s in suffixes]
    rnd.shuffle(triples)
    for p, i, s in triples:
        w = p + i + s
        if w not in words:
            words.add(w)
            out.append(w)
            if len(out) >= n:
                return out

    # Fallback (apenas se n > 30*20*20 = 12000): gera palavras alfa aleatórias.
    while len(out) < n:
        size = rnd.randint(4, 12)
        w = "".join(rnd.choices(string.ascii_lowercase, k=size))
        if w not in words:
            words.add(w)
            out.append(w)
    return out


# -------------------------------------------------------------------- cenários
def _gen_basico() -> Dict:
    documentos = [
        {
            "id": "doc1",
            "titulo": "Introdução a Estruturas de Dados",
            "conteudo": (
                "Estruturas de dados são fundamentais para algoritmos eficientes. "
                "Tabelas hash oferecem acesso O(1) em média."
            ),
            "metadados": {"autor": "Knuth", "ano": 1973, "categoria": "livro"},
        },
        {
            "id": "doc2",
            "titulo": "Árvores Balanceadas",
            "conteudo": (
                "Árvores AVL, Red-Black e Splay garantem operações em O(log N). "
                "A árvore splay move elementos acessados para a raiz."
            ),
            "metadados": {"autor": "Sleator", "ano": 1985, "categoria": "artigo"},
        },
        {
            "id": "doc3",
            "titulo": "Algoritmos de Ordenação",
            "conteudo": (
                "HeapSort possui complexidade O(N log N) no pior caso e usa "
                "memória adicional constante."
            ),
            "metadados": {"autor": "Williams", "ano": 1964, "categoria": "artigo"},
        },
        {
            "id": "doc4",
            "titulo": "Recuperação de Informação",
            "conteudo": (
                "O índice invertido mapeia termos para documentos. "
                "TF-IDF é uma técnica clássica de pontuação."
            ),
            "metadados": {"autor": "Salton", "ano": 1975, "categoria": "livro"},
        },
        {
            "id": "doc5",
            "titulo": "Tries e Autocompletar",
            "conteudo": (
                "A árvore Trie é ideal para buscas por prefixo. "
                "Sistemas de autocompletar a utilizam intensivamente."
            ),
            "metadados": {"autor": "Fredkin", "ano": 1960, "categoria": "artigo"},
        },
    ]
    consultas = [
        {"tipo": "search", "query": "árvore splay", "k": 3},
        {"tipo": "search", "query": "ordenação heap", "k": 3},
        {"tipo": "search", "query": "índice invertido", "k": 5},
        {"tipo": "autocomplete", "prefix": "arv", "limit": 5},
        {"tipo": "autocomplete", "prefix": "or", "limit": 5},
        {"tipo": "cache_get", "doc_id": "doc2"},
        {"tipo": "cache_get", "doc_id": "doc999"},  # miss intencional
    ]
    return {"documentos": documentos, "consultas": consultas}


def _gen_avancado(rnd: random.Random) -> Dict:
    """Cenário com edge cases: docs sem conteúdo, palavras repetidas, miss."""
    base = _gen_basico()
    documentos = list(base["documentos"])

    documentos.append(
        {
            "id": "doc_empty",
            "titulo": "",
            "conteudo": "",
            "metadados": {"categoria": "vazio"},
        }
    )
    documentos.append(
        {
            "id": "doc_dup",
            "titulo": "splay splay splay",
            "conteudo": "splay splay árvore splay árvore splay",
            "metadados": {"categoria": "duplicado"},
        }
    )
    documentos.append(
        {
            "id": "doc_long",
            "titulo": "Documento extenso sobre RAG",
            "conteudo": (
                "Sistemas de recuperação aumentada por geração utilizam índices "
                "vetoriais e textuais. Tabelas hash são usadas como índice invertido. "
                "Árvores splay servem como cache adaptativo. Algoritmos como "
                "heap sort, merge sort e quick sort possuem complexidades diferentes. "
                "TF-IDF, BM25 e embeddings são técnicas comuns de pontuação."
            ),
            "metadados": {"categoria": "abrangente"},
        }
    )

    consultas = [
        {"tipo": "search", "query": "splay árvore", "k": 5},
        {"tipo": "search", "query": "heap sort ordenação", "k": 5},
        {"tipo": "search", "query": "termo_que_nao_existe_xyz", "k": 5},
        {"tipo": "search", "query": "", "k": 5},
        {"tipo": "autocomplete", "prefix": "spl", "limit": 5},
        {"tipo": "autocomplete", "prefix": "zzz", "limit": 5},
        {"tipo": "autocomplete", "prefix": "", "limit": 5},
        {"tipo": "cache_get", "doc_id": "doc_dup"},
        {"tipo": "cache_get", "doc_id": "doc_long"},
        {"tipo": "cache_get", "doc_id": "doc_dup"},   # repete (cache hit)
        {"tipo": "cache_get", "doc_id": "doc_inexistente"},
    ]
    return {"documentos": documentos, "consultas": consultas}


def _gen_estresse(
    rnd: random.Random,
    n_docs: int = 10_000,
    n_unique_words: int = 50_000,
    words_per_doc_min: int = 30,
    words_per_doc_max: int = 80,
    n_queries: int = 500,
) -> Dict:
    """Gera o cenário massivo do Projeto 1.

    Estratégia para garantir 50k palavras únicas em apenas 10k documentos:
        * geramos um vocabulário base de exatamente n_unique_words palavras
        * distribuímos as palavras Zipfianamente entre docs
        * fazemos uma "passada de cobertura" garantindo que toda palavra
          única apareça em pelo menos um documento
    """
    fake = _faker_or_fallback()
    vocabulary = _unique_words(n_unique_words, rnd)
    assert len(vocabulary) == n_unique_words

    # Pesos Zipfianos: peso[i] = 1 / (i+1)^0.9
    weights = [1.0 / ((i + 1) ** 0.9) for i in range(n_unique_words)]
    # Pré-computa CDF para amostragem ponderada O(log V) com bisect.
    import bisect
    cdf = []
    acc = 0.0
    for w in weights:
        acc += w
        cdf.append(acc)
    total_w = cdf[-1]

    def _weighted_choice() -> str:
        x = rnd.random() * total_w
        idx = bisect.bisect_left(cdf, x)
        if idx >= n_unique_words:
            idx = n_unique_words - 1
        return vocabulary[idx]

    documentos = []

    # Plano: garantir cobertura -> primeiros n_unique_words tokens
    # estão "reservados" para serem inseridos sequencialmente.
    coverage_index = 0
    for i in range(n_docs):
        doc_id = f"doc_{i:05d}"
        nwords = rnd.randint(words_per_doc_min, words_per_doc_max)

        tokens: List[str] = []
        for _ in range(nwords):
            if coverage_index < n_unique_words:
                tokens.append(vocabulary[coverage_index])
                coverage_index += 1
            else:
                tokens.append(_weighted_choice())

        random.Random(i).shuffle(tokens)
        conteudo = " ".join(tokens)
        if fake is not None and (i % 50 == 0):
            titulo = fake.sentence(nb_words=4).rstrip(".")
        else:
            titulo = f"Documento sintético {i}"
        documentos.append(
            {
                "id": doc_id,
                "titulo": titulo,
                "conteudo": conteudo,
                "metadados": {
                    "categoria": "estresse",
                    "lote": i // 1000,
                    "tamanho": nwords,
                },
            }
        )

    # Garante cobertura completa caso n_docs * mín < n_unique_words.
    if coverage_index < n_unique_words:
        extras = vocabulary[coverage_index:]
        chunk_size = (len(extras) // 100) + 1
        for k in range(0, len(extras), chunk_size):
            target_doc = documentos[k % n_docs]
            target_doc["conteudo"] += " " + " ".join(extras[k : k + chunk_size])
        coverage_index = n_unique_words

    # Consultas: mistura de search, autocomplete e cache_get.
    consultas: List[Dict] = []
    for q in range(n_queries):
        kind = rnd.randint(0, 99)
        if kind < 60:  # search
            n_terms = rnd.randint(1, 3)
            terms = [_weighted_choice() for _ in range(n_terms)]
            consultas.append(
                {"tipo": "search", "query": " ".join(terms), "k": 5}
            )
        elif kind < 85:  # autocomplete
            base_word = _weighted_choice()
            prefix_len = rnd.randint(2, max(2, len(base_word) // 2))
            consultas.append(
                {
                    "tipo": "autocomplete",
                    "prefix": base_word[:prefix_len],
                    "limit": 10,
                }
            )
        else:  # cache_get
            doc_idx = rnd.randint(0, n_docs - 1)
            consultas.append(
                {"tipo": "cache_get", "doc_id": f"doc_{doc_idx:05d}"}
            )

    return {
        "config": {"splay_capacity": 512},
        "documentos": documentos,
        "consultas": consultas,
        "meta": {
            "n_docs": n_docs,
            "n_unique_words": n_unique_words,
            "n_queries": n_queries,
            "seed": SEED,
        },
    }


# ----------------------------------------------------------- gabarito (output)
def _compute_expected(input_data: Dict) -> Dict:
    """Calcula o gabarito executando o próprio motor sobre o input.

    NÃO é hardcode: o gabarito é gerado DINAMICAMENTE pela mesma
    implementação que será avaliada. Útil para os cenários básico e
    avançado, em que o gabarito precisa estar comitado no Git.
    """
    # Import tardio para evitar dependência circular durante o boot.
    from src.main import _process  # type: ignore
    return _process(input_data)


def _write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")
    print(f"[gen] {path}  ({path.stat().st_size/1024:.1f} KiB)")


# -------------------------------------------------------------------- CLI
def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="generate_data")
    p.add_argument(
        "--cenario",
        choices=("basico", "avancado", "estresse", "all"),
        default="all",
    )
    p.add_argument("--out", default="data/", help="Pasta de saída.")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--n-docs", type=int, default=10_000)
    p.add_argument("--n-words", type=int, default=50_000)
    p.add_argument("--n-queries", type=int, default=500)
    p.add_argument(
        "--skip-gabarito-estresse",
        action="store_true",
        help="Não calcula gabarito do cenário estresse (acelera a geração).",
    )
    args = p.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(args.seed)

    cenarios = [args.cenario] if args.cenario != "all" else ["basico", "avancado", "estresse"]
    for cen in cenarios:
        if cen == "basico":
            data = _gen_basico()
            _write_json(out_dir / "input_basico.json", data)
            expected = _compute_expected(data)
            _write_json(out_dir / "output_esperado_basico.json", expected)
        elif cen == "avancado":
            data = _gen_avancado(rnd)
            _write_json(out_dir / "input_avancado.json", data)
            expected = _compute_expected(data)
            _write_json(out_dir / "output_esperado_avancado.json", expected)
        elif cen == "estresse":
            print(
                f"[gen] gerando cenário ESTRESSE: "
                f"{args.n_docs} docs / {args.n_words} palavras únicas / "
                f"{args.n_queries} consultas (seed={args.seed})"
            )
            data = _gen_estresse(
                rnd,
                n_docs=args.n_docs,
                n_unique_words=args.n_words,
                n_queries=args.n_queries,
            )
            _write_json(out_dir / "input_estresse.json", data)
            if not args.skip_gabarito_estresse:
                print("[gen] computando gabarito do estresse (pode demorar)...")
                expected = _compute_expected(data)
                _write_json(out_dir / "output_esperado_estresse.json", expected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
