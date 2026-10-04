#!/bin/sh
# Rainmath installer for Arch Linux, Manjaro, EndeavourOS, Garuda and other pacman based distros.
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/common.sh"
parse_args "$@"
preflight

PKGS="python python-pip tk ttf-dejavu"

if python_ready; then
    say "Python, pip, venv and Tk are already there, skipping system packages."
else
    say "Packages to install with pacman: $PKGS"
    confirm "Continue?" || die "Cancelled."
    # no -Sy on purpose: refreshing the database without a full upgrade can break Arch
    # shellcheck disable=SC2086
    as_root pacman -S --needed --noconfirm $PKGS \
        || die "pacman failed. If it says 'target not found', update your system first: sudo pacman -Syu"
fi

need_python
setup_venv
verify
make_shortcut
finish
