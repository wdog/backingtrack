#!/usr/bin/env bash
# backingtrack — installer per Linux e macOS (rilanciato = aggiornamento)
#
#   curl -fsSL https://raw.githubusercontent.com/wdog/backingtrack/main/install.sh | bash
#
# Variabili opzionali:
#   BT_BASS=1         installa anche il contrabbasso (~56 MB)
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
# versione installata (se c'è) e versione che sta per arrivare
ver_of() { sed -n 's/^__version__ = "\(.*\)"/\1/p'; }
OLD=""; have backingtrack && OLD="$(backingtrack --version 2>/dev/null | awk '{print $NF}')" || true
NEW=""
if [ -n "${BT_SRC:-}" ] && [ -f "${BT_SRC}/backingtrack/__init__.py" ]; then
  NEW="$(ver_of < "${BT_SRC}/backingtrack/__init__.py")"
elif have curl; then
  NEW="$(curl -fsSL "https://raw.githubusercontent.com/${REPO}/${REF}/backingtrack/__init__.py" 2>/dev/null | ver_of)" || true
fi
if [ -n "$OLD" ] && [ -n "$NEW" ]; then
  if [ "$OLD" = "$NEW" ]; then step "Reinstallo backingtrack $NEW (già l'ultima)"; else step "Aggiorno backingtrack $OLD → $NEW"; fi
else
  step "Installo backingtrack${NEW:+ $NEW}"
fi
BIN="$HOME/.local/bin"
PKG="$ZIP"
if [ -n "${BT_SRC:-}" ] || have git; then PKG="$SRC"; fi
if have pipx; then
  # reinstallazione pulita (vale anche come aggiornamento): i campioni stanno altrove e restano.
  # --system-site-packages: la GUI usa PyGObject/GTK installati dal sistema
  pipx uninstall backingtrack >/dev/null 2>&1 || true
  pipx install --system-site-packages "$PKG" >/dev/null 2>&1 || die "pipx install fallito"
  BTPY="$(pipx environment --value PIPX_LOCAL_VENVS)/backingtrack/bin/python"
  ok "installato con pipx"
else
  DATA="${XDG_DATA_HOME:-$HOME/.local/share}/backingtrack"
  [ "$OS" = Darwin ] && DATA="$HOME/Library/Application Support/backingtrack"
  VENV="$DATA/venv"
  if ! "$PY" -m venv --clear --system-site-packages "$VENV" >/dev/null 2>&1; then
    if [ "$OS" = Linux ] && have apt-get && ask "Manca python3-venv: lo installo?"; then
      install_pkg python3-venv python3-pip
      "$PY" -m venv --clear --system-site-packages "$VENV"
    else
      die "impossibile creare il virtualenv (su Debian/Ubuntu: sudo apt install python3-venv)"
    fi
  fi
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q --upgrade "$PKG"
  mkdir -p "$BIN"
  ln -sf "$VENV/bin/backingtrack" "$BIN/backingtrack"
  BTPY="$VENV/bin/python"
  ok "installato in $VENV"
fi

BT="$BIN/backingtrack"
have backingtrack && BT="$(command -v backingtrack)"
[ -x "$BT" ] || die "installazione non riuscita: comando backingtrack non trovato"
ok "comando: $BT ($("$BT" --version))"

# voce nel menu applicazioni (Linux): icona dal pacchetto installato + file .desktop
if [ "$OS" = Linux ]; then
  APP_ID="io.github.wdog.backingtrack"
  SHARE="${XDG_DATA_HOME:-$HOME/.local/share}"
  PKGDIR="$("$BTPY" -c 'import backingtrack, os; print(os.path.dirname(backingtrack.__file__))')"
  mkdir -p "$SHARE/icons/hicolor/256x256/apps" "$SHARE/applications"
  cp "$PKGDIR/data/$APP_ID.png" "$SHARE/icons/hicolor/256x256/apps/"
  cat > "$SHARE/applications/$APP_ID.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=backingtrack
Comment=Backing track da accordi: chitarra, batteria e contrabbasso
Exec=$BT gui %f
Icon=$APP_ID
Terminal=false
Categories=AudioVideo;Audio;Music;
StartupWMClass=$APP_ID
EOF
  have update-desktop-database && update-desktop-database -q "$SHARE/applications" || true
  ok "menu applicazioni: $SHARE/applications/$APP_ID.desktop"
fi

# ---------------------------------------------------------------- campioni
if [ "${BT_NO_SAMPLES:-0}" = 1 ]; then
  warn "campioni saltati: più tardi esegui  backingtrack setup"
else
  step "Scarico i campioni (chitarre + batteria + casse, ~460 MB)"
  # i pacchetti già presenti vengono saltati: rilanciare l'installer = aggiornare
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
    backingtrack gui                     editor grafico
    backingtrack new mia_canzone.yaml    oppure da terminale
    backingtrack mia_canzone.yaml --mp3
    backingtrack doctor                  controlla che sia tutto a posto
    backingtrack update                  aggiornamenti futuri

  ${D}Esempi: https://github.com/${REPO}/tree/${REF}/examples${N}
  ${D}Guida:  https://github.com/${REPO}#readme${N}

EOF
