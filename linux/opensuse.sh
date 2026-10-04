#!/bin/sh
# Rainmath installer for openSUSE Tumbleweed, Leap and other zypper based distros.
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/common.sh"
parse_args "$@"
preflight

PKGS="python3 python3-pip python3-tk dejavu-fonts"
# Leap ships Python 3.6 as "python3", too old: fall back to the python311 packages
PKGS_NEW="python311 python311-pip python311-tk dejavu-fonts"

if python_ready; then
    say "Python, pip, venv and Tk are already there, skipping system packages."
else
    say "Packages to install with zypper: $PKGS"
    confirm "Continue?" || die "Cancelled."
    # shellcheck disable=SC2086
    as_root zypper --non-interactive install $PKGS || warn "zypper could not install every package."
    if ! python_ready; then
        warn "The default python3 is too old or incomplete, trying the python311 packages."
        # shellcheck disable=SC2086
        as_root zypper --non-interactive install $PKGS_NEW || die "zypper install failed."
    fi
fi

need_python
setup_venv
verify
make_shortcut
finish
