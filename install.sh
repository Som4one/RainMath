#!/bin/sh
# Rainmath Linux installer: detects your distro and runs the matching script in linux/.
#   ./install.sh                 auto-detect
#   ./install.sh arch -y         force a distro, no questions asked
DIR=$(cd "$(dirname "$0")" && pwd)

target=""
for a in "$@"; do
    case "$a" in
        debian|arch|fedora|opensuse|alpine) target="$a" ;;
        -h|--help) exec sh "$DIR/linux/debian.sh" --help ;;
    esac
done

if [ -z "$target" ]; then
    ID=""; ID_LIKE=""
    # shellcheck disable=SC1090
    [ -r "${OS_RELEASE:-/etc/os-release}" ] && . "${OS_RELEASE:-/etc/os-release}"
    case " $ID $ID_LIKE " in
        *" arch "*|*" manjaro "*|*" artix "*)           target=arch ;;
        *" debian "*|*" ubuntu "*|*" linuxmint "*)      target=debian ;;
        *" fedora "*|*" rhel "*|*" centos "*)           target=fedora ;;
        *suse*)                                         target=opensuse ;;
        *" alpine "*)                                   target=alpine ;;
    esac
fi

# unknown distro name: fall back on the package manager that is installed
if [ -z "$target" ]; then
    if   command -v pacman  >/dev/null 2>&1; then target=arch
    elif command -v apt-get >/dev/null 2>&1; then target=debian
    elif command -v dnf     >/dev/null 2>&1; then target=fedora
    elif command -v zypper  >/dev/null 2>&1; then target=opensuse
    elif command -v apk     >/dev/null 2>&1; then target=alpine
    fi
fi

if [ -z "$target" ]; then
    echo "Could not detect a supported distro (Debian/Ubuntu, Arch, Fedora/RHEL, openSUSE, Alpine)." >&2
    echo "Pick one by hand, for example:  ./install.sh arch" >&2
    echo "Or install by hand: Python 3.9+, pip, venv and Tk, then" >&2
    echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python Rainmath.py" >&2
    exit 1
fi

[ "${RAINMATH_DETECT_ONLY:-0}" = 1 ] && { echo "$target"; exit 0; }
exec sh "$DIR/linux/$target.sh" "$@"
