#!/bin/sh
# Rainmath installer for Fedora, RHEL, Rocky, AlmaLinux, CentOS Stream, Nobara and other dnf based distros.
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/common.sh"
parse_args "$@"
preflight

PKGS="python3 python3-pip python3-tkinter dejavu-sans-fonts dejavu-sans-mono-fonts"

if python_ready; then
    say "Python, pip, venv and Tk are already there, skipping system packages."
else
    say "Packages to install with dnf: $PKGS"
    confirm "Continue?" || die "Cancelled."
    # shellcheck disable=SC2086
    as_root dnf install -y $PKGS || die "dnf install failed."
fi

need_python
setup_venv
verify
make_shortcut
finish
