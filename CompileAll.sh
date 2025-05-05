#!/usr/bin/env bash
set -e
shopt -s nullglob

# where this script lives (i.e. projects/11)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# path to your compiler driver
COMPILER="$SCRIPT_DIR/JackCompiler.py"

echo
echo "Starting compilation of every .jack under $SCRIPT_DIR"
echo

for DIR in "$SCRIPT_DIR"/*/; do
  [ -d "$DIR" ] || continue
  echo "=============================================================="
  echo "Directory: $DIR"
  for JACK in "$DIR"/*.jack; do
    [ -f "$JACK" ] || continue
    VM="${JACK%.jack}.vm"
    echo "  Compiling $(basename "$JACK") → $(basename "$VM")"
    python3 "$COMPILER" "$JACK"
  done
  echo
done

echo "All .jack files have been compiled to .vm"
