#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Script padrão de execução do Motor RAG Local.
#
# Uso:
#   ./run.sh <arquivo_input.json> <arquivo_output.json>
#
# Exemplos:
#   ./run.sh data/input_basico.json    data/output_real_basico.json
#   ./run.sh data/input_avancado.json  data/output_real_avancado.json
#   ./run.sh data/input_estresse.json  data/output_real_estresse.json
# ---------------------------------------------------------------------------
set -euo pipefail

INPUT_FILE="${1:-data/input_basico.json}"
OUTPUT_FILE="${2:-output.json}"

PYTHON_BIN="${PYTHON_BIN:-python3}"

# Garante que o pacote src/ seja descoberto independente do diretório atual.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

"$PYTHON_BIN" -m src.main --input "$INPUT_FILE" --output "$OUTPUT_FILE"
