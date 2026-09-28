#!/usr/bin/env bash
# Uruchomienie jednym kliknięciem (macOS: dwa razy kliknij ten plik; Linux: też, jeśli włączysz "Wykonywalny")
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo
  echo "  Nie znaleziono Pythona 3. Zainstaluj go (macOS: brew install python; Ubuntu: sudo apt install python3)."
  echo
  read -r -p "  Enter, aby zamknąć..." _
  exit 1
fi
PORT="${PORT:-8000}"
echo
echo "  Uruchamiam aplikację na http://localhost:$PORT — zostaw to okno otwarte."
echo
( sleep 1; (command -v open >/dev/null && open "http://localhost:$PORT") || (command -v xdg-open >/dev/null && xdg-open "http://localhost:$PORT") ) &
exec "$PY" server.py --port "$PORT"
