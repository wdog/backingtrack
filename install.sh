#!/usr/bin/env bash
# backingtrack — installer per Linux e macOS
#
#   curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash
#
# Variabili opzionali:
#   BT_BASS=1         installa anche il contrabbasso (~265 MB)
#   BT_NO_SAMPLES=1   non scaricare i campioni adesso
#   BT_YES=1          non chiedere conferme (installa ffmpeg se manca)
#   BT_REF=main       branch/tag da installare
set -euo pipefail

REPO="wdog/backingtrack"
REF="${BT_REF:-main}"
SRC="${BT_SRC:-git+https://github.com/${REPO}.git@${REF}}"   # BT_SRC=. per installare da una copia locale
ZIP="https://github.com/${REPO}/archive/${REF}.zip"

if [ -t 1 ]; then
  B=$'\033[1m'; D=$'\033[2m'; R=$'\033[31m'; G=$'\033[32m'; Y=$'\033[33m'; O=$'\033[38;5;214m'; N=$'\033[0m'
else
  B=; D=; R=; G=; Y=; O=; N=
fi
step() { printf '\n%s▸ %s%s\n' "$O$B" "$*" "$N"; }
ok()   { printf '  %s✓%s %s\n' "$G" "$N" "$*"; }
warn() { printf '  %s!%s %s\n' "$Y" "$N" "$*"; }
die()  { printf '\n%s✗ %s%s\n' "$R$B" "$*" "$N" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# domande anche con "curl | bash" (stdin è lo script): leggiamo dal terminale
ask() {
  [ "${BT_YES:-0}" = 1 ] && return 0
  [ -r /dev/tty ] || return 1
  local reply
  printf '  %s [S/n] ' "$1" > /dev/tty
  read -r reply < /dev/tty || return 1
  case "$reply" in n|N|no|NO) return 1 ;; *) return 0 ;; esac
}

cat <<EOF
${O}${B}
   ♪  backingtrack
      rock · blues · rockabilly
      chitarra e batteria vere, dai tuoi accordi${N}
EOF

# ---------------------------------------------------------------- sistema
step "Controllo il sistema"
OS="$(uname -s)"
case "$OS" in
  Linux|Darwin) ok "sistema: $OS $(uname -m)" ;;
  *) die "sistema non supportato: $OS (su Windows usa install.ps1)" ;;
esac

PY=""
for c in python3 python; do
  if have "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -n "$PY" ] || die "serve Python 3.8 o superiore (https://www.python.org/downloads/)"
ok "python: $($PY --version 2>&1)"

SUDO=""
[ "$(id -u)" -ne 0 ] && have sudo && SUDO="sudo"

install_pkg() {  # $@ = pacchetti
  if [ "$OS" = Darwin ]; then
    have brew || die "installa Homebrew (https://brew.sh) oppure ffmpeg a mano"
    brew install "$@"
  elif have apt-get; then $SUDO apt-get update -qq && $SUDO apt-get install -y "$@"
  elif have dnf; then $SUDO dnf install -y "$@"
  elif have pacman; then $SUDO pacman -S --noconfirm "$@"
  elif have zypper; then $SUDO zypper install -y "$@"
  elif have apk; then $SUDO apk add "$@"
  else return 1
  fi
}

if have ffmpeg; then
  ok "ffmpeg: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
else
  warn "ffmpeg non trovato"
  if ask "Installo ffmpeg con il gestore pacchetti?"; then
    install_pkg ffmpeg || die "non so installare ffmpeg qui: installalo a mano e rilancia"
    ok "ffmpeg installato"
  else
    die "ffmpeg è necessario. Installalo (es. sudo apt install ffmpeg / brew install ffmpeg) e rilancia"
  fi
fi

# ---------------------------------------------------------------- programma
step "Installo backingtrack"
BIN="$HOME/.local/bin"
PKG="$ZIP"
if [ -n "${BT_SRC:-}" ] || have git; then PKG="$SRC"; fi
if have pipx; then
  pipx install --force "$PKG" >/dev/null 2>&1 || die "pipx install fallito"
  ok "installato con pipx"
else
  DATA="${XDG_DATA_HOME:-$HOME/.local/share}/backingtrack"
  [ "$OS" = Darwin ] && DATA="$HOME/Library/Application Support/backingtrack"
  VENV="$DATA/venv"
  if ! "$PY" -m venv "$VENV" >/dev/null 2>&1; then
    if [ "$OS" = Linux ] && have apt-get && ask "Manca python3-venv: lo installo?"; then
      install_pkg python3-venv python3-pip
      "$PY" -m venv "$VENV"
    else
      die "impossibile creare il virtualenv (su Debian/Ubuntu: sudo apt install python3-venv)"
    fi
  fi
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q --upgrade "$PKG"
  mkdir -p "$BIN"
  ln -sf "$VENV/bin/backingtrack" "$BIN/backingtrack"
  ok "installato in $VENV"
fi

BT="$BIN/backingtrack"
have backingtrack && BT="$(command -v backingtrack)"
[ -x "$BT" ] || die "installazione non riuscita: comando backingtrack non trovato"
ok "comando: $BT ($("$BT" --version))"

# ---------------------------------------------------------------- campioni
if [ "${BT_NO_SAMPLES:-0}" = 1 ]; then
  warn "campioni saltati: più tardi esegui  backingtrack setup"
else
  step "Scarico i campioni (chitarra + batteria, ~370 MB)"
  if [ "${BT_BASS:-0}" = 1 ]; then "$BT" setup --bass; else "$BT" setup; fi
fi

# ---------------------------------------------------------------- fine
step "Fatto!"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) warn "$BIN non è nel PATH. Aggiungi al tuo ~/.bashrc o ~/.zshrc:"
     # shellcheck disable=SC2016
     printf '      export PATH="%s:$PATH"\n' "$BIN" ;;
esac
cat <<EOF

  ${B}Prova subito:${N}
    backingtrack new mia_canzone.yaml
    backingtrack mia_canzone.yaml --mp3

  ${D}Esempi: https://github.com/${REPO}/tree/${REF}/examples${N}
  ${D}Guida:  https://github.com/${REPO}#readme${N}

EOF
