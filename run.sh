#!/usr/bin/env bash
# ---------------------------------------------------------------
# Pavimentos AASHTO '93 — levanta la app en local
#
#   ./run.sh         modo uso: compila la interfaz (si hace falta) y abre http://localhost:8000
#   ./run.sh dev     modo desarrollo: API con recarga + Vite en http://localhost:5173
# ---------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"

if [ "${1:-}" = "dev" ]; then
  uv run uvicorn api.main:app --port 8000 --reload --reload-dir api --reload-dir pavimentos &
  API=$!
  trap 'kill $API 2>/dev/null' EXIT
  (cd web && pnpm install --silent && pnpm dev)
  exit
fi

if [ ! -f web/dist/index.html ] || [ -n "$(find web/src web/index.html -newer web/dist/index.html 2>/dev/null | head -1)" ]; then
  echo "▸ Compilando la interfaz…"
  (cd web && pnpm install --silent && pnpm build)
fi
( sleep 2 && command -v xdg-open >/dev/null && xdg-open http://localhost:8000 >/dev/null 2>&1 ) &
echo "▸ App en http://localhost:8000  (Ctrl+C para cerrar)"
uv run uvicorn api.main:app --port 8000
