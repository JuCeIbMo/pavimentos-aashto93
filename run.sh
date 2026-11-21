#!/usr/bin/env bash
# ---------------------------------------------------------------
# Pavimentos AASHTO '93 — levanta la app Streamlit
#
# Uso:
#   ./run.sh          # abre en http://localhost:8501 y abre el navegador
#   ./run.sh 8600     # abre en otro puerto
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

PUERTO="${1:-8501}"

if command -v uv >/dev/null 2>&1; then
  uv run streamlit run app/app.py --server.port "$PUERTO"
elif [ -x ".venv/bin/streamlit" ]; then
  ".venv/bin/streamlit" run app/app.py --server.port "$PUERTO"
else
  echo "❌ No encontré 'uv' ni el entorno '.venv'." >&2
  echo "   Instalá las dependencias una vez con:  uv pip install -e \".[dev]\"" >&2
  exit 1
fi
