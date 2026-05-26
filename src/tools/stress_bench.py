"""Benchmark de carga.

Mede tempo de execução e pico de memória ao processar um arquivo de input
massivo. Usado como prova de carga (critério 6 da rubrica).

Uso:
    python -m src.tools.stress_bench --input data/input_estresse.json
"""

from __future__ import annotations

import argparse
import json
import resource
import time
from pathlib import Path

from ..main import _process


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    args = p.parse_args()

    in_path = Path(args.input)
    print(f"[stress] lendo {in_path} ({in_path.stat().st_size / 1024 / 1024:.2f} MiB)")

    t0 = time.perf_counter()
    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    t_load = time.perf_counter() - t0
    print(f"[stress] JSON carregado em {t_load*1000:.1f}ms")

    t0 = time.perf_counter()
    payload = _process(data)
    elapsed = time.perf_counter() - t0

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS usa bytes, Linux usa kilobytes — normalizamos para MiB.
    import sys

    if sys.platform == "darwin":
        rss_mib = rss / 1024 / 1024
    else:
        rss_mib = rss / 1024

    stats = payload["estatisticas"]
    print("[stress] -------- resultados --------")
    print(f"  documentos indexados : {stats['indice_invertido']['documents']}")
    print(f"  termos únicos        : {stats['indice_invertido']['vocabulary']}")
    print(f"  total de consultas   : {stats['total_consultas']}")
    print(f"  tempo de indexação   : {stats['tempo_indexacao_ms']} ms")
    print(f"  tempo de consultas   : {stats['tempo_consultas_ms']} ms")
    print(f"  tempo total processo : {elapsed*1000:.1f} ms")
    print(f"  pico de memória RSS  : {rss_mib:.1f} MiB")
    print(
        f"  hash load_factor     : {stats['indice_invertido']['hash_index']['load_factor']}"
    )
    print(f"  trie nodes           : {stats['trie']['nodes']}")
    print(f"  splay size           : {stats['cache_splay']['size']}")
    print(f"  splay hits / misses  : {stats['cache_splay']['hits']} / {stats['cache_splay']['misses']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
