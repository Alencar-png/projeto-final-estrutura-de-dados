"""CLI principal do Motor RAG Local.

Uso:
    python -m src.main --input <arquivo_input.json> --output <arquivo_output.json>

Formato do input.json:
{
  "documentos": [
    {"id": "doc1", "titulo": "...", "conteudo": "...", "metadados": {...}},
    ...
  ],
  "consultas": [
    {"tipo": "search",       "query": "termos da busca", "k": 5},
    {"tipo": "autocomplete", "prefix": "pa", "limit": 10},
    {"tipo": "cache_get",    "doc_id": "doc1"}
  ]
}

Formato do output.json:
{
  "resultados": [
    {"id": 0, "tipo": "search",       "query": "...", "top_k": [...]},
    {"id": 1, "tipo": "autocomplete", "prefix": "...", "sugestoes": [...]},
    {"id": 2, "tipo": "cache_get",    "doc_id": "...", "metadados": {...}}
  ],
  "estatisticas": {...}
}
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from .engine import RAGEngine


def _load_input(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _process(data: Dict[str, Any]) -> Dict[str, Any]:
    documentos = data.get("documentos", [])
    consultas = data.get("consultas", [])
    if not isinstance(documentos, list):
        raise ValueError("'documentos' precisa ser uma lista.")
    if not isinstance(consultas, list):
        raise ValueError("'consultas' precisa ser uma lista.")

    engine = RAGEngine(splay_capacity=data.get("config", {}).get("splay_capacity", 256))

    t_ingest_start = time.perf_counter()
    engine.ingest_documents(documentos)
    t_ingest_ms = (time.perf_counter() - t_ingest_start) * 1000

    resultados: List[Dict[str, Any]] = []
    t_query_total = 0.0
    for idx, query in enumerate(consultas):
        tipo = query.get("tipo")
        t0 = time.perf_counter()
        if tipo == "search":
            q = query.get("query", "")
            k = int(query.get("k", 5))
            top = engine.search(q, k=k)
            resultados.append(
                {"id": idx, "tipo": "search", "query": q, "k": k, "top_k": top}
            )
        elif tipo == "autocomplete":
            prefix = query.get("prefix", "")
            limit = int(query.get("limit", 10))
            sugestoes = engine.autocomplete(prefix, limit=limit)
            resultados.append(
                {
                    "id": idx,
                    "tipo": "autocomplete",
                    "prefix": prefix,
                    "limit": limit,
                    "sugestoes": sugestoes,
                }
            )
        elif tipo == "cache_get":
            doc_id = query.get("doc_id", "")
            meta = engine.cache_get(doc_id)
            resultados.append(
                {
                    "id": idx,
                    "tipo": "cache_get",
                    "doc_id": doc_id,
                    "metadados": meta if meta is not None else None,
                }
            )
        else:
            resultados.append(
                {"id": idx, "tipo": tipo, "erro": f"tipo de consulta desconhecido: {tipo!r}"}
            )
        t_query_total += time.perf_counter() - t0

    stats = engine.stats()
    stats["tempo_indexacao_ms"] = round(t_ingest_ms, 3)
    stats["tempo_consultas_ms"] = round(t_query_total * 1000, 3)
    stats["total_consultas"] = len(consultas)

    return {"resultados": resultados, "estatisticas": stats}


def _write_output(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="motor-rag",
        description="Motor RAG Local — Projeto Final de Estrutura de Dados.",
    )
    parser.add_argument("--input", required=True, help="Arquivo JSON de entrada.")
    parser.add_argument("--output", required=True, help="Arquivo JSON de saída.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Não imprime estatísticas no stdout.",
    )
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    out_path = Path(args.output)
    if not in_path.exists():
        print(f"ERRO: arquivo de entrada não encontrado: {in_path}", file=sys.stderr)
        return 2

    data = _load_input(in_path)

    t0 = time.perf_counter()
    payload = _process(data)
    elapsed = time.perf_counter() - t0

    _write_output(out_path, payload)

    if not args.quiet:
        stats = payload["estatisticas"]
        print(
            f"[OK] {in_path.name} -> {out_path.name}"
            f" | docs={stats['indice_invertido']['documents']}"
            f" | vocab={stats['indice_invertido']['vocabulary']}"
            f" | consultas={stats['total_consultas']}"
            f" | indexacao={stats['tempo_indexacao_ms']}ms"
            f" | consultas={stats['tempo_consultas_ms']}ms"
            f" | total={round(elapsed*1000,1)}ms"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
