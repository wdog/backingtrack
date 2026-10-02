"""Output colorato per il terminale (doctor, update, setup, remove): palette Dracula come la GUI."""
import os
import re
import shutil
import sys
import unicodedata

PURPLE, PINK, GREEN, ORANGE = "#bd93f9", "#ff79c6", "#50fa7b", "#ffb86c"
CYAN, RED, YELLOW, COMMENT = "#8be9fd", "#ff5555", "#f1fa8c", "#6272a4"
WIDTH = 66
_ANSI = re.compile(r"\033\[[0-9;]*m")


def enabled():
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def paint(color, text, bold=False):
    """Testo nel colore '#rrggbb' (truecolor), solo se l'output è un terminale."""
    if not enabled() or not color:
        return str(text)
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return "\033[%s38;2;%d;%d;%dm%s\033[0m" % ("1;" if bold else "", r, g, b, text)


def dim(text):
    return paint(COMMENT, text)


def bold(text):
    return "\033[1m%s\033[0m" % text if enabled() else str(text)


def width(text):
    """Larghezza visibile: senza codici ANSI, emoji larghe 2."""
    plain = _ANSI.sub("", str(text))
    return sum(0 if unicodedata.combining(ch) or ch == "️" else
               2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in plain)


def cols():
    return max(40, min(WIDTH, shutil.get_terminal_size((WIDTH, 20)).columns - 2))


def _mix(a, b, t):
    pa, pb = (int(a[i:i + 2], 16) for i in (1, 3, 5)), (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))


def gradient(text, a=PURPLE, b=PINK, bold_=True):
    """Testo sfumato carattere per carattere (viola → rosa)."""
    if not enabled():
        return text
    n = max(len(text) - 1, 1)
    return "".join(paint(_mix(a, b, i / n), ch, bold_) for i, ch in enumerate(text))


def bar(frac, size=24):
    """Barra piena per `frac` (0…1), sfumata viola → rosa, il resto in grigio."""
    n = round(size * max(0.0, min(frac, 1.0)))
    if not enabled():
        return "#" * n + "-" * (size - n)
    return gradient("━" * n, bold_=False) + dim("─" * (size - n))


def box(lines, color=PURPLE):
    """Riquadro con angoli arrotondati attorno alle righe."""
    w = max(cols(), max(width(l) for l in lines) + 4)
    print(paint(color, "╭" + "─" * (w - 2) + "╮"))
    for l in lines:
        print(paint(color, "│") + "  " + l + " " * (w - 4 - width(l)) + paint(color, "│"))
    print(paint(color, "╰" + "─" * (w - 2) + "╯"))


def banner(subtitle):
    """Intestazione: ♪ backingtrack X.Y.Z · subtitle."""
    from . import __version__
    print()
    box([gradient("♪ backingtrack %s" % __version__) + dim("  ·  ") + paint(CYAN, subtitle)])


def section(title, right=""):
    """◆ Titolo ──────────── testo a destra"""
    left = paint(PINK, "◆", True) + " " + bold(title) + " "
    room = cols() - width(left) - 5
    if len(right) > room:  # percorsi lunghi: tengo la fine
        right = "…" + right[-room + 1:]
    right = (" " + dim(right)) if right else ""
    fill = max(3, cols() - width(left) - width(right))
    print("\n" + left + dim("─" * fill) + right)


OK, BAD, WARN, OFF, DOWN, DOT = "✓", "✗", "!", "·", "↓", "•"
MARK_COLORS = {OK: GREEN, BAD: RED, WARN: YELLOW, OFF: COMMENT, DOWN: PURPLE, DOT: CYAN}


def row(mark, label, value="", extra="", label_width=12):
    """  ✓ etichetta    valore  dettagli"""
    value = str(value)
    if mark == OFF:
        value = dim(value)
    pad = " " * max(1, label_width - width(label))
    print("  %s %s%s%s%s" % (paint(MARK_COLORS.get(mark), mark, True), bold(label) if mark != OFF else dim(label),
                             pad, value, ("  " + dim(extra)) if extra else ""))


def note(text):
    """Riga di dettaglio rientrata, in grigio."""
    print("      " + dim(text))


def done(text, hint=""):
    """Riquadro verde finale."""
    print()
    box([paint(GREEN, "✓ " + text, True)] + ([dim(hint)] if hint else []), GREEN)


def todo(title, items):
    """Riquadro giallo con la lista numerata di cose da fare: [(cosa, comando)]."""
    print()
    lines = [paint(YELLOW, "! " + title, True)]
    for i, (what, cmd) in enumerate(items, 1):
        lines += ["%s %s" % (paint(YELLOW, "%d." % i), what), "   " + paint(CYAN, cmd)]
    box(lines, YELLOW)
