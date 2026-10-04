#!/bin/sh
# Shared helpers for the Rainmath Linux installers. Sourced by the distro scripts, not run directly.
# Plain POSIX sh on purpose, so it also works on Alpine (no bash needed).

ROOT=$(cd "$HERE/.." && pwd)
VENV="$ROOT/.venv"
ASSUME_YES=0
MAKE_SHORTCUT=1
VENV_FLAGS=""
PYTHON=""

if [ -t 1 ]; then
    C_B=$(printf '\033[36m'); C_G=$(printf '\033[32m'); C_Y=$(printf '\033[33m'); C_R=$(printf '\033[31m'); C_0=$(printf '\033[0m')
else
    C_B=""; C_G=""; C_Y=""; C_R=""; C_0=""
fi

say()  { printf '%s[Rainmath]%s %s\n' "$C_B" "$C_0" "$*"; }
ok()   { printf '%s[Rainmath]%s %s\n' "$C_G" "$C_0" "$*"; }
warn() { printf '%s[Rainmath]%s %s\n' "$C_Y" "$C_0" "$*" >&2; }
die()  { printf '%s[Rainmath] ERROR:%s %s\n' "$C_R" "$C_0" "$*" >&2; exit 1; }

usage() {
    cat <<USAGE
Usage: ./install.sh [distro] [options]

  distro        debian | arch | fedora | opensuse | alpine   (auto-detected if omitted)

Options:
  -y, --yes         do not ask before installing system packages
  --no-shortcut     do not create the application menu entry
  -h, --help        show this help
USAGE
}

parse_args() {
    for a in "$@"; do
        case "$a" in
            -y|--yes) ASSUME_YES=1 ;;
            --no-shortcut) MAKE_SHORTCUT=0 ;;
            -h|--help) usage; exit 0 ;;
        esac
    done
}

preflight() {
    if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ]; then
        die "Do not run this with sudo. Run ./install.sh as your normal user, it asks for sudo only when needed."
    fi
    [ -f "$ROOT/Rainmath.py" ] || die "Rainmath.py not found in $ROOT"
    [ -f "$ROOT/requirements.txt" ] || die "requirements.txt not found in $ROOT"
}

confirm() {
    [ "$ASSUME_YES" -eq 1 ] && return 0
    printf '%s [Y/n] ' "$1"
    read -r r || r=y
    case "$r" in n|N|no|NO) return 1 ;; *) return 0 ;; esac
}

as_root() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    elif command -v doas >/dev/null 2>&1; then
        doas "$@"
    else
        die "Root rights are needed to install packages, but neither sudo nor doas was found. Run this script as root."
    fi
}

# Python 3.9+ with tkinter. Sets $PYTHON.
find_python() {
    PYTHON=""
    for c in python3 python3.13 python3.12 python3.11 python3.10 python3.9 python; do
        command -v "$c" >/dev/null 2>&1 || continue
        if "$c" -c 'import sys, tkinter; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
            PYTHON=$(command -v "$c")
            return 0
        fi
    done
    return 1
}

# Python is usable if it is 3.9+, has tkinter, and can build a venv with pip.
python_ready() {
    find_python && "$PYTHON" -c 'import venv, ensurepip' >/dev/null 2>&1
}

need_python() {
    find_python || die "No Python 3.9+ with Tk found after installing packages. Your distro release may be too old (Python 3.9 is the minimum)."
    say "Using $("$PYTHON" --version 2>&1) ($PYTHON)"
}

setup_venv() {
    if [ -x "$VENV/bin/python" ] && ! "$VENV/bin/python" -c 'import tkinter' >/dev/null 2>&1; then
        warn "Existing .venv is broken, recreating it."
        rm -rf "$VENV"
    fi
    if [ ! -x "$VENV/bin/python" ]; then
        say "Creating virtual environment in $VENV"
        rm -rf "$VENV"
        # shellcheck disable=SC2086
        "$PYTHON" -m venv $VENV_FLAGS "$VENV" || die "Could not create the virtual environment (is the python venv package installed?)."
    fi
    "$VENV/bin/python" -m pip --version >/dev/null 2>&1 || "$VENV/bin/python" -m ensurepip --upgrade || die "pip is not available in the virtual environment."
    say "Upgrading pip"
    "$VENV/bin/python" -m pip install --upgrade pip >/dev/null 2>&1 || warn "Could not upgrade pip, continuing with the bundled one."
    say "Installing Python libraries (this can take a few minutes)"
    "$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt" || die "pip failed to install the libraries, see the messages above."
}

verify() {
    "$VENV/bin/python" -c 'import tkinter, customtkinter, sympy, numpy, matplotlib, PIL' \
        || die "A library does not import correctly."
    ok "All dependencies are installed."
}

make_shortcut() {
    [ "$MAKE_SHORTCUT" -eq 1 ] || return 0
    chmod +x "$ROOT/run.sh" 2>/dev/null || true
    dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$dir" || { warn "Could not create $dir, skipping the menu entry."; return 0; }
    cat > "$dir/rainmath.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Rainmath
Comment=Math toolbox with symbolic computation
Exec="$ROOT/run.sh"
Path=$ROOT
Icon=accessories-calculator
Terminal=false
Categories=Education;Science;Math;
DESKTOP
    command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$dir" >/dev/null 2>&1
    ok "Menu entry created: $dir/rainmath.desktop"
}

finish() {
    ok "Done."
    say "Start Rainmath with:  $ROOT/run.sh"
    [ "$MAKE_SHORTCUT" -eq 1 ] && say "or look for \"Rainmath\" in your application menu."
    return 0
}
