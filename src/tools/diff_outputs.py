"""Compara o arquivo de saída real com o esperado (gabarito).

Uso:
    python -m src.tools.diff_outputs <esperado.json> <real.json>

Compara o campo `resultados` (estritamente, item-a-item).
O campo `estatisticas` é IGNORADO porque depende do hardware (tempos).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2:
        print("Uso: python -m src.tools.diff_outputs <esperado.json> <real.json>")
        return 2
    expected = _load(Path(argv[0])).get("resultados", [])
    actual = _load(Path(argv[1])).get("resultados", [])

    if expected == actual:
        print(f"[OK] Saídas coincidem ({len(expected)} resultados).")
        return 0

    print(f"[FAIL] Diferenças encontradas.")
    print(f"  esperado: {len(expected)} resultados")
    print(f"  real:     {len(actual)} resultados")
    diff_count = 0
    for i, (e, a) in enumerate(zip(expected, actual)):
        if e != a:
            diff_count += 1
            if diff_count <= 5:
                print(f"\n--- Diff #{i} ---")
                print("Esperado:", json.dumps(e, ensure_ascii=False, indent=2))
                print("Real:    ", json.dumps(a, ensure_ascii=False, indent=2))
    if diff_count > 5:
        print(f"... e mais {diff_count - 5} divergências.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
