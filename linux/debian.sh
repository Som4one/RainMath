#!/bin/sh
# Rainmath installer for Debian, Ubuntu, Linux Mint, Pop!_OS, Kali, Raspberry Pi OS and other apt based distros.
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/common.sh"
parse_args "$@"
preflight

PKGS="python3 python3-pip python3-venv python3-tk fonts-dejavu-core"

if python_ready; then
    say "Python, pip, venv and Tk are already there, skipping system packages."
else
    say "Packages to install with apt: $PKGS"
    confirm "Continue?" || die "Cancelled."
    as_root apt-get update || warn "apt-get update failed, trying to install anyway."
    # shellcheck disable=SC2086
    as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y $PKGS || die "apt-get install failed."
fi

need_python
setup_venv
verify
make_shortcut
finish
