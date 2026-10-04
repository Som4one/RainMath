#!/bin/sh
# Starts Rainmath with the virtual environment created by install.sh
DIR=$(cd "$(dirname "$(readlink -f "$0")")" && pwd)
cd "$DIR" || exit 1
if [ ! -x .venv/bin/python ]; then
    echo "Rainmath is not installed yet. Run ./install.sh first." >&2
    exit 1
fi
exec .venv/bin/python Rainmath.py "$@"
