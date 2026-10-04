#!/bin/sh
# Removes the virtual environment and the menu entry. Your files and reglages.json are kept.
DIR=$(cd "$(dirname "$0")" && pwd)
rm -rf "$DIR/.venv"
rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/applications/rainmath.desktop"
echo "Rainmath environment and menu entry removed. System packages were left alone."
