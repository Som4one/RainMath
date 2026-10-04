#!/bin/sh
# Rainmath installer for Alpine Linux and postmarketOS (apk based, musl).
# numpy, matplotlib, pillow and sympy come from apk (prebuilt for musl), the rest from pip.
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/common.sh"
parse_args "$@"
preflight

PKGS="python3 py3-pip py3-tkinter py3-numpy py3-matplotlib py3-pillow py3-sympy font-dejavu"
VENV_FLAGS="--system-site-packages"

if python_ready && python3 -c 'import numpy, matplotlib, PIL, sympy' >/dev/null 2>&1; then
    say "Python and the scientific libraries are already there, skipping system packages."
else
    say "Packages to install with apk: $PKGS"
    confirm "Continue?" || die "Cancelled."
    # shellcheck disable=SC2086
    as_root apk add $PKGS || die "apk add failed."
fi

need_python
setup_venv
verify
make_shortcut
finish
