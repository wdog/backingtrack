"""Editor grafico GTK4 / libadwaita: crea, modifica, valida, genera e ascolta i brani.

Avvio:  backingtrack gui   oppure   backingtrack-gui [file.yaml]
Serve PyGObject con GTK 4 e libadwaita (Debian/Ubuntu: sudo apt install python3-gi gir1.2-adw-1).
"""
import re
import sys
import threading
import traceback
from pathlib import Path

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    gi.require_version("PangoCairo", "1.0")
    from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango, PangoCairo
except (ImportError, ValueError) as _e:  # pragma: no cover
    Gtk = None
    _GI_ERROR = _e

from . import __version__, packs
from . import songfile as sf
from .errors import SongError
from .grooves import GROOVES
from .song import build_timeline, load_song
from .theory import Chord

APP_ID = "io.github.wdog.backingtrack"
GROOVE_NAMES = list(GROOVES)
SWING_HINT = "0 = ottavi dritti · 0.5 = swing leggero · 1 = shuffle terzinato"
TRI = ["dal groove", "sì", "no"]
TRI_VAL = [None, True, False]

SECTION_COLORS = ["#e8591a", "#2f9bd8", "#2ec27e", "#c061cb", "#f5c211", "#e01b8a", "#1abc9c", "#8b6fdc"]
STYLE_EMOJI = {"rock": "🤘", "blues": "🎷", "rockabilly": "🕺", "country": "🤠"}

CSS = ("""
:root { --accent-bg-color: #e8811a; --accent-fg-color: #ffffff; --accent-color: #f5a623; }
@define-color accent_bg_color #e8811a;
@define-color accent_fg_color #ffffff;
@define-color accent_color #f5a623;
button.suggested-action { background-color: #e8811a; color: white; }
button.suggested-action:hover { background-color: #f0922e; }
button.suggested-action:disabled { background-color: alpha(#e8811a, 0.35); }
.navigation-sidebar > row:selected { background-color: alpha(#e8811a, 0.30); }
switch:checked { background-color: #e8811a; }
viewswitcher button:checked, stackswitcher button:checked { color: #f5a623; }
entry:focus-within { outline-color: alpha(#f5a623, 0.7); }
.emoji { font-size: 1.25em; min-width: 1.6em; }
.dot { font-size: 1.4em; }
.status-ok { color: @success_color; }
.status-bad { color: @warning_color; }
.big-emoji { font-size: 3.5em; }
.render-btn { font-weight: bold; }
.bar-num { font-size: 0.8em; opacity: 0.6; font-feature-settings: "tnum"; }
.bar-entry { font-weight: bold; font-size: 1.1em; }
.bar-reading { font-size: 0.8em; opacity: 0.75; }
.yaml-view { font-family: monospace; padding: 12px; }
.summary { padding: 4px 12px; }
.player { padding: 10px 16px; background: alpha(#e8811a, 0.08); border-top: 1px solid alpha(#e8811a, 0.35); }
.play-btn { min-width: 52px; min-height: 52px; -gtk-icon-size: 24px; }
.player-title { font-weight: bold; }
.player-time { font-feature-settings: "tnum"; opacity: 0.7; font-size: 0.9em; }
.player scale highlight { background: #e8811a; }
.player scale slider { background: #f5a623; }
.picker { font-weight: 600; }
.bar-grid { margin-top: 4px; }
.bar-cell { padding: 4px 6px 4px 4px; border-radius: 6px; background: alpha(currentColor, 0.06);
            border-left: 4px solid alpha(currentColor, 0.3); min-height: 34px; }
.bar-cell.bad { background: alpha(@error_color, 0.18); border-left-color: @error_color; }
.bar-cell.drop-hover, .bar-add.drop-hover { background: alpha(#e8811a, 0.35); }
.bar-cell entry { background: transparent; box-shadow: none; min-height: 26px; padding: 0 2px; }
.bar-handle { opacity: 0.35; font-size: 1.1em; padding: 0 2px; }
.bar-handle:hover { opacity: 0.9; }
.bar-add { min-height: 34px; font-size: 1.2em; }
.chip { padding: 2px 10px; min-height: 26px; border-radius: 13px; font-weight: bold; }
.chip-main { background: alpha(#e8811a, 0.25); padding: 4px 14px; }
toggle-group { background: alpha(currentColor, 0.08); border-radius: 10px; padding: 3px; }
toggle-group > toggle { padding: 4px 11px; margin: 0 1px; border-radius: 8px; font-weight: 600; min-height: 24px; }
toggle-group > toggle:hover { background: alpha(currentColor, 0.08); }
toggle-group > toggle:checked { background: #e8811a; color: #ffffff; }
toggle-group > separator { background: transparent; min-width: 0; }
.grid-choice { min-width: 44px; font-weight: 600; }
.wave { border-radius: 8px; background: alpha(currentColor, 0.06); }
.builder { padding: 12px; }
""" + "".join(
    ".sec-%d.bar-cell { border-left-color: %s; background: alpha(%s, 0.10); } .sec-%d.dot { color: %s; }\n"
    % (i, c, c, i, c) for i, c in enumerate(SECTION_COLORS))).encode()

# --------------------------------------------------------------------------- widget di supporto

def spin_row(title, lo, hi, step, digits=0, subtitle=None):
    row = Adw.SpinRow.new_with_range(lo, hi, step)
    row.set_title(title)
    row.set_digits(digits)
    if subtitle:
        row.set_subtitle(subtitle)
    return row


def deco(row, emoji):
    """Emoji colorata davanti a una riga di impostazioni."""
    lab = Gtk.Label(label=emoji)
    lab.add_css_class("emoji")
    row.add_prefix(lab)
    return row


def style_emoji(groove):
    return STYLE_EMOJI.get((groove or "").split("/")[0], "🎵")


def groove_text(name):
    return "%s %s" % (style_emoji(name), sf.groove_label(name))


def labeled_button(icon, label, tooltip, callback, *args):
    b = Gtk.Button(tooltip_text=tooltip)
    b.set_child(Adw.ButtonContent(icon_name=icon, label=label))
    b.add_css_class("flat")
    b.connect("clicked", lambda _b: callback(*args))
    return b


def icon_button(icon, tooltip, callback, *args):
    b = Gtk.Button(icon_name=icon, tooltip_text=tooltip)
    b.add_css_class("flat")
    b.connect("clicked", lambda _b: callback(*args))
    return b


STYLE_NAMES = {"rock": "Rock", "blues": "Blues", "rockabilly": "Rockabilly", "country": "Country"}


class MenuRow(Adw.ActionRow):
    """Riga con un pulsante-menu a sottomenu (al posto di una tendina lunga e stretta).

    Interfaccia come Adw.ComboRow: proprietà 'selected', get_selected/set_selected, notify::selected.
    names: valori (indice = selected); groups: [(etichetta sottomenu, [nomi])]; top: nomi fuori dai sottomenu.
    """
    selected = GObject.Property(type=int, default=0)

    def __init__(self, title, names, groups, top=(), item_label=str, button_label=str, subtitle=None):
        super().__init__(title=title)
        self.names, self.button_label, self.subtitle_fn = list(names), button_label, subtitle
        self.action = Gio.SimpleAction.new_stateful("pick", GLib.VariantType.new("s"),
                                                    GLib.Variant.new_string(self.names[0]))
        self.action.connect("change-state", self._picked)
        group = Gio.SimpleActionGroup()
        group.add_action(self.action)
        self.insert_action_group("row", group)

        def item(n):
            it = Gio.MenuItem.new(item_label(n), None)
            it.set_action_and_target_value("row.pick", GLib.Variant.new_string(n))
            return it

        menu = Gio.Menu()
        if top:
            sec = Gio.Menu()
            for n in top:
                sec.append_item(item(n))
            menu.append_section(None, sec)
        if groups:
            sec = Gio.Menu()
            for label, members in groups:
                sub = Gio.Menu()
                for n in members:
                    sub.append_item(item(n))
                sec.append_submenu(label, sub)
            menu.append_section(None, sec)

        self.label = Gtk.Label(ellipsize=3, max_width_chars=24,
                               width_chars=min(18, max(len(button_label(n)) for n in self.names)))
        self.button = Gtk.MenuButton(menu_model=menu, valign=Gtk.Align.CENTER, always_show_arrow=True)
        self.button.add_css_class("picker")
        self.button.set_child(self.label)
        self.add_suffix(self.button)
        self.set_activatable_widget(self.button)
        self.set_subtitle_lines(3)
        self.connect("notify::selected", lambda *_a: self._sync())
        self._sync()

    def get_selected(self):
        return self.props.selected

    def set_selected(self, i):
        self.props.selected = i
        self._sync()

    def _picked(self, _action, value):
        if value.get_string() in self.names:
            self.props.selected = self.names.index(value.get_string())

    def refresh_inherited(self):
        self._sync()

    def _sync(self):
        i = self.props.selected
        name = self.names[i] if 0 <= i < len(self.names) else self.names[0]
        self.action.set_state(GLib.Variant.new_string(name))
        self.label.set_label(self.button_label(name))
        if self.subtitle_fn:
            self.set_subtitle(GLib.markup_escape_text(self.subtitle_fn(name) or ""))


def GrooveRow(title, inherit=False, song_groove=None):
    by_style = {}
    for n in GROOVE_NAMES:
        by_style.setdefault(n.split("/")[0], []).append(n)
    groups = [("%s  %s" % (STYLE_EMOJI.get(st, "🎵"), STYLE_NAMES.get(st, st.title())), names)
              for st, names in by_style.items()]
    desc = lambda n: GROOVES[n]["desc"].split(":", 1)[-1].strip()

    def subtitle(n):
        if n:
            return desc(n)
        g = song_groove() if song_groove else None
        return "dal brano: %s — %s" % (g, desc(g)) if g in GROOVES else ""

    return MenuRow(title, ([""] if inherit else []) + GROOVE_NAMES, groups,
                   top=[""] if inherit else (),
                   item_label=lambda n: "🎵 come il brano" if not n else "%s — %s" % (n, desc(n)),
                   button_label=lambda n: "🎵 come il brano" if not n else "%s %s" % (style_emoji(n), n),
                   subtitle=subtitle)


TEMPLATE_GROUPS = [
    ("🎷  Blues", ["12-bar blues (quick change)", "12-bar blues", "8-bar blues", "Blues minore",
                  "Slow blues con passaggi", "Turnaround I-IV-I-V", "Un accordo (boogie)"]),
    ("🤘  Rock", ["Rock'n'roll I-IV-V (12)", "Rock I-bVII-IV", "Minore i-bVII-bVI-V"]),
    ("🕺  Anni '50 e pop", ["Anni '50 I-vi-IV-V", "Pop-rock I-V-vi-IV"]),
]


def ChoiceRow(title, options, subtitle=None):
    """Menu a tendina compatto: options = [(etichetta, descrizione)]. Stessa interfaccia di ComboRow."""
    labels = [lab for lab, _d in options]
    desc = dict(options)
    return MenuRow(title, labels, [], top=labels,
                   item_label=lambda n: "%s — %s" % (n, desc[n]) if desc[n] else n,
                   button_label=lambda n: n, subtitle=(lambda n: subtitle) if subtitle else None)


class GridPicker(Gtk.MenuButton):
    """Pulsante che apre una griglia di scelte (note, tipi di accordo, sezioni)."""
    selected = GObject.Property(type=int, default=0)

    def __init__(self, labels, rows, tooltips=None, fmt=None, columns_hint=None):
        super().__init__(valign=Gtk.Align.CENTER, always_show_arrow=True)
        self.add_css_class("picker")
        self.labels, self.fmt = labels, fmt or (lambda i: labels[i])
        self.lab = Gtk.Label()
        self.set_child(self.lab)
        pop = Gtk.Popover()
        grid = Gtk.Grid(row_spacing=4, column_spacing=4, margin_start=6, margin_end=6, margin_top=6, margin_bottom=6)
        self.buttons = {}
        for r, row in enumerate(rows):
            for c, i in enumerate(row):
                if i is None:
                    continue
                b = Gtk.Button(label=labels[i])
                b.add_css_class("grid-choice")
                if tooltips and tooltips[i]:
                    b.set_tooltip_text(tooltips[i])
                b.connect("clicked", self._pick, i)
                span = columns_hint if (columns_hint and len(row) == 1) else 1
                grid.attach(b, c, r, span, 1)
                self.buttons[i] = b
        pop.set_child(grid)
        self.set_popover(pop)
        self.connect("notify::selected", lambda *_a: self._sync())
        self._sync()

    def _pick(self, _b, i):
        self.props.selected = i
        self.popdown()

    def get_selected(self):
        return self.props.selected

    def set_selected(self, i):
        self.props.selected = i
        self._sync()

    def _sync(self):
        i = self.props.selected
        self.lab.set_label(self.fmt(i) if 0 <= i < len(self.labels) else "—")
        for j, b in self.buttons.items():
            (b.add_css_class if j == i else b.remove_css_class)("suggested-action")


def note_rows(names, offset=0):
    """Griglia di note: naturali, diesis, bemolle."""
    idx = {n: i + offset for i, n in enumerate(names)}
    rows = [[idx.get(n) for n in "C D E F G A B".split()],
            [idx.get(n) for n in "C# D# F# G# A#".split()],
            [idx.get(n) for n in "Db Eb Gb Ab Bb".split()]]
    return [[i for i in r if i is not None] for r in rows]


class PickerRow(Adw.ActionRow):
    """Riga con un GridPicker come suffisso; 'selected' della riga = quello del picker."""
    selected = GObject.Property(type=int, default=0)

    def __init__(self, title, picker):
        super().__init__(title=title)
        self.picker = picker
        picker.bind_property("selected", self, "selected",
                             GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE)
        self.add_suffix(picker)
        self.set_activatable_widget(picker)

    def get_selected(self):
        return self.props.selected

    def set_selected(self, i):
        self.picker.set_selected(i)


def drag_source(widget, payload, icon_widget=None):
    """Rende trascinabile un widget: payload è una stringa ('chord:A7' o 'bar:3')."""
    src = Gtk.DragSource(actions=Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
    src.connect("prepare", lambda _s, _x, _y: Gdk.ContentProvider.new_for_value(payload()))
    src.connect("drag-begin", lambda s, _d: s.set_icon(Gtk.WidgetPaintable.new(icon_widget or widget), 0, 0))
    widget.add_controller(src)


def drop_target(widget, on_drop):
    tgt = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
    tgt.connect("enter", lambda *_a: widget.add_css_class("drop-hover") or Gdk.DragAction.COPY)
    tgt.connect("leave", lambda *_a: widget.remove_css_class("drop-hover"))

    def drop(_t, value, _x, _y):
        widget.remove_css_class("drop-hover")
        return on_drop(value)
    tgt.connect("drop", drop)
    widget.add_controller(tgt)


class BarCell(Gtk.Box):
    """Una battuta nella griglia: maniglia ⠿ (trascina per spostare), numero, accordi.

    Si possono trascinare accordi dalla tavolozza sopra la cella. Tasto destro = menu.
    """

    def __init__(self, editor, index, text, color):
        super().__init__(spacing=4)
        self.editor, self.index = editor, index
        self.add_css_class("bar-cell")
        self.add_css_class("sec-%d" % color)
        handle = Gtk.Label(label="⠿", tooltip_text="Trascina per spostare la battuta")
        handle.add_css_class("bar-handle")
        handle.set_cursor(Gdk.Cursor.new_from_name("grab"))
        drag_source(handle, lambda: "bar:%d" % index, self)
        self.append(handle)
        num = Gtk.Label(label=str(index + 1), valign=Gtk.Align.START)
        num.add_css_class("bar-num")
        self.append(num)
        self.entry = Gtk.Entry(text=text, width_chars=3, max_width_chars=14, hexpand=True, has_frame=False,
                               placeholder_text="—")
        self.entry.add_css_class("bar-entry")
        self.entry.connect("changed", self._changed)
        self.entry.connect("activate", lambda _e: editor.focus_bar(index + 1, create=True))
        focus = Gtk.EventControllerFocus()
        focus.connect("enter", lambda _c: editor.set_focused_bar(index))
        self.entry.add_controller(focus)
        self.append(self.entry)
        drop_target(self, lambda value: editor.drop_on_bar(index, value))

        # menu tasto destro
        group = Gio.SimpleActionGroup()
        for name, fn in (("dup", editor.duplicate_bar), ("del", editor.remove_bar),
                         ("before", lambda i: editor.insert_bar(i)), ("after", lambda i: editor.insert_bar(i + 1)),
                         ("clear", lambda i: self.entry.set_text(""))):
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", lambda _a, _p, f=fn: f(index))
            group.add_action(act)
        self.insert_action_group("bar", group)
        menu = Gio.Menu()
        menu.append("Duplica battuta", "bar.dup")
        menu.append("Inserisci battuta prima", "bar.before")
        menu.append("Inserisci battuta dopo", "bar.after")
        menu.append("Svuota", "bar.clear")
        menu.append("Elimina battuta", "bar.del")
        self.popover = Gtk.PopoverMenu.new_from_model(menu)
        self.popover.set_parent(self)
        click = Gtk.GestureClick(button=3)
        click.connect("pressed", self._context)
        self.add_controller(click)
        self.validate()

    def _context(self, _g, _n, x, y):
        rect = Gdk.Rectangle()
        rect.x, rect.y, rect.width, rect.height = int(x), int(y), 1, 1
        self.popover.set_pointing_to(rect)
        self.popover.popup()

    def do_unrealize(self):
        self.popover.unparent()
        Gtk.Box.do_unrealize(self)

    def _changed(self, entry):
        self.editor.bar_changed(self.index, entry.get_text())
        self.validate()

    def validate(self):
        text = self.entry.get_text()
        err = sf.check_bar(text, self.index == 0) if text.strip() else None
        (self.add_css_class if err else self.remove_css_class)("bad")
        reading = sf.describe_bar(text, self.index == 0) if text.strip() and not err else "battuta vuota"
        tip = ("⚠ " + err) if err else "Battuta %d: %s\n\n%s" % (self.index + 1, reading, sf.BAR_HELP)
        self.set_tooltip_text(tip)


def fmt_time(us):
    sec = max(0, int(us // 1_000_000))
    return "%d:%02d" % (sec // 60, sec % 60)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def song_bars(song, sections):
    """Battute nel tempo, per la striscia accordi del player: [{start, dur, segs, section, color, first}]."""
    order, timeline = build_timeline(song)
    bar = 240 / float(song.get("tempo", 120))
    names = [s["name"] for s in sections]
    bars, t = [], 0.0
    if song.get("count_in", True):
        bars.append(dict(start=0.0, dur=bar, segs=[(0, 4, "1 · 2 · 3 · 4")], section="conteggio", color=None, first=True))
        t = bar
    first_chord = None
    for b in timeline:
        segs = [(s0, d, c.name if c else "N.C.") for s0, d, c in b["segs"]]
        first_chord = first_chord or next((c.name for _, _, c in b["segs"] if c), None)
        name = b["sec"]["name"]
        bars.append(dict(start=t, dur=bar, segs=segs, section=name, first=b["first"],
                         color=names.index(name) % len(SECTION_COLORS) if name in names else None))
        t += bar
    if song.get("ending", True) and first_chord:
        end = song.get("ending_chord")
        end = Chord(str(end), int(song.get("transpose", 0))).name if end else first_chord
        bars.append(dict(start=t, dur=bar * 2, segs=[(0, 4, end)], section="finale", color=None, first=True))
    return bars


class ChordStrip(Gtk.DrawingArea):
    """Battute con accordi che scorrono con la musica; la corrente è evidenziata. Clic = salta lì."""

    def __init__(self, player):
        super().__init__(hexpand=True)
        self.player = player
        self.bars = []
        self.set_size_request(-1, 64)
        self.set_draw_func(self._draw)
        click = Gtk.GestureClick()
        click.connect("pressed", self._click)
        self.add_controller(click)
        self.set_tooltip_text("Clicca una battuta per saltare lì")
        self._view = (0, 1, 1)

    def current(self, t):
        for i, b in enumerate(self.bars):
            if b["start"] <= t < b["start"] + b["dur"]:
                return i
        return len(self.bars) - 1 if self.bars and t >= self.bars[-1]["start"] else 0

    def _text(self, cr, text, font, x, y, w, rgba):
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(Pango.FontDescription.from_string(font))
        layout.set_text(text, -1)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_width(int(max(1, w) * Pango.SCALE))
        _ink, logical = layout.get_pixel_extents()
        cr.set_source_rgba(*rgba)
        cr.move_to(x + max(0, (w - logical.width) / 2), y)
        PangoCairo.show_layout(cr, layout)
        return logical.height

    def _draw(self, _area, cr, w, h):
        if not self.bars:
            return
        fg = self.get_color()
        ink = (fg.red, fg.green, fg.blue)
        m = self.player.media
        t = m.get_timestamp() / 1e6 if m else 0
        cur = self.current(t)
        n = max(3, min(len(self.bars), int(w // 120)))
        start = max(0, min(cur - 1, len(self.bars) - n))
        bw = w / n
        self._view = (start, bw, n)
        top = 16
        for i in range(start, min(len(self.bars), start + n)):
            b = self.bars[i]
            x = (i - start) * bw + 3
            bwi = bw - 6
            if i == cur:
                cr.set_source_rgba(0.91, 0.51, 0.10, 0.38)
            else:
                cr.set_source_rgba(*ink, 0.05 if i < cur else 0.10)
            self._round(cr, x, top, bwi, h - top - 2, 7)
            cr.fill()
            if b["color"] is not None:
                cr.set_source_rgba(*hex_rgb(SECTION_COLORS[b["color"]]), 0.95)
                cr.rectangle(x + 4, top, bwi - 8, 3)
                cr.fill()
            if b["first"]:
                col = hex_rgb(SECTION_COLORS[b["color"]]) if b["color"] is not None else ink
                self._text(cr, b["section"], "Sans Bold 8", x, 1, bwi, (*col, 0.95))
            for s0, d, name in b["segs"]:
                sx = x + s0 / 4 * bwi
                sw = d / 4 * bwi
                if s0 > 0:
                    cr.set_source_rgba(*ink, 0.25)
                    cr.rectangle(sx, top + 10, 1, h - top - 20)
                    cr.fill()
                font = "Sans Bold 14" if i == cur else "Sans Bold 12"
                alpha = 1.0 if i >= cur else 0.45
                self._text(cr, name, font, sx + 2, top + (h - top) / 2 - 11, sw - 4, (*ink, alpha))
            if i == cur and b["dur"]:
                frac = max(0, min(1, (t - b["start"]) / b["dur"]))
                cr.set_source_rgba(0.96, 0.65, 0.14, 1)
                cr.rectangle(x + 4, h - 6, (bwi - 8) * frac, 3)
                cr.fill()

    @staticmethod
    def _round(cr, x, y, w, h, r):
        import math
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def _click(self, _g, _n, x, _y):
        start, bw, n = self._view
        i = start + int(x // bw)
        m = self.player.media
        if m and 0 <= i < len(self.bars):
            m.seek(int(self.bars[i]["start"] * 1e6))
            self.queue_draw()


class Player(Gtk.Revealer):
    """Barra di riproduzione: pulsanti grandi, forma d'onda cliccabile, tempo, volume."""

    def __init__(self, win):
        super().__init__(transition_type=Gtk.RevealerTransitionType.SLIDE_UP, reveal_child=False)
        self.win = win
        self.media = None
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.add_css_class("player")
        box = Gtk.Box(spacing=14)

        self.btn_restart = self._button("media-skip-backward-symbolic", "Da capo (B)", self.restart)
        self.btn_play = self._button("media-playback-start-symbolic", "Play / pausa (Spazio)", self.toggle)
        self.btn_play.add_css_class("play-btn")
        self.btn_play.add_css_class("suggested-action")
        self.btn_stop = self._button("media-playback-stop-symbolic", "Stop (S)", self.stop)
        for b in (self.btn_restart, self.btn_play, self.btn_stop):
            box.append(b)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        self.title = Gtk.Label(xalign=0, ellipsize=3, max_width_chars=26, width_chars=18)
        self.title.add_css_class("player-title")
        self.time = Gtk.Label(xalign=0, label="0:00 / 0:00")
        self.time.add_css_class("player-time")
        info.append(self.title)
        info.append(self.time)
        box.append(info)

        # forma d'onda + avanzamento disegnato sopra
        self.wave = Gtk.Picture(content_fit=Gtk.ContentFit.FILL, can_shrink=True, hexpand=True)
        self.progress = Gtk.DrawingArea(hexpand=True)
        self.progress.set_draw_func(self._draw)
        overlay = Gtk.Overlay(hexpand=True)
        overlay.set_size_request(200, 56)
        overlay.add_css_class("wave")
        overlay.set_child(self.wave)
        overlay.add_overlay(self.progress)
        overlay.set_tooltip_text("Clicca o trascina per spostarti nel brano")
        click = Gtk.GestureClick()
        click.connect("pressed", lambda _g, _n, x, _y: self._seek_x(x))
        drag = Gtk.GestureDrag()
        drag.connect("drag-update", self._drag)
        overlay.add_controller(click)
        overlay.add_controller(drag)
        self.overlay = overlay
        box.append(overlay)

        vol = Gtk.Box(spacing=4, valign=Gtk.Align.CENTER)
        vol.append(Gtk.Image.new_from_icon_name("audio-volume-high-symbolic"))
        self.volume = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.05)
        self.volume.set_value(1)
        self.volume.set_size_request(90, -1)
        self.volume.connect("value-changed", lambda sc: self.media and self.media.set_volume(sc.get_value()))
        vol.append(self.volume)
        box.append(vol)
        box.append(self._button("folder-open-symbolic", "Apri la cartella dei file generati", win.open_output_dir))
        outer.append(box)
        self.strip = ChordStrip(self)
        outer.append(self.strip)
        self.set_child(outer)

    @staticmethod
    def _button(icon, tip, cb):
        b = Gtk.Button(icon_name=icon, tooltip_text=tip, valign=Gtk.Align.CENTER)
        b.add_css_class("circular")
        b.connect("clicked", lambda _b: cb())
        return b

    def load(self, wav, title, wave_png=None, bars=None):
        self.strip.bars = bars or []
        if self.media:
            self.media.pause()
        self.media = Gtk.MediaFile.new_for_filename(str(wav))
        self.media.set_volume(self.volume.get_value())
        self.media.connect("notify::timestamp", self._tick)
        self.media.connect("notify::duration", self._tick)
        self.media.connect("notify::playing", self._update_icon)
        self.title.set_label("♪ " + title)
        self.wave.set_filename(str(wave_png) if wave_png else None)
        self.set_reveal_child(True)
        self.media.play()

    def _tick(self, *_a):
        m = self.media
        self.time.set_label("%s / %s" % (fmt_time(m.get_timestamp()), fmt_time(m.get_duration())))
        self.progress.queue_draw()
        self.strip.queue_draw()

    def _update_icon(self, *_a):
        playing = self.media is not None and self.media.get_playing()
        self.btn_play.set_icon_name("media-playback-pause-symbolic" if playing else "media-playback-start-symbolic")

    def _draw(self, _area, cr, w, h):
        m = self.media
        frac = m.get_timestamp() / m.get_duration() if m and m.get_duration() else 0
        x = frac * w
        cr.set_source_rgba(0, 0, 0, 0.45)  # parte non ancora suonata più scura
        cr.rectangle(x, 0, w - x, h)
        cr.fill()
        cr.set_source_rgba(0.96, 0.65, 0.14, 0.18)
        cr.rectangle(0, 0, x, h)
        cr.fill()
        dur = m.get_duration() / 1e6 if m and m.get_duration() else 0
        for b in self.strip.bars if dur else ():
            if b["first"] and b["color"] is not None:
                cr.set_source_rgba(*hex_rgb(SECTION_COLORS[b["color"]]), 0.9)
                cr.rectangle(b["start"] / dur * w - 1, 0, 2, h)
                cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.9)
        cr.rectangle(x - 1, 0, 2, h)
        cr.fill()

    def _seek_x(self, x):
        m = self.media
        w = self.overlay.get_width()
        if m and m.get_duration() and w:
            m.seek(int(max(0, min(1, x / w)) * m.get_duration()))
            self.progress.queue_draw()

    def _drag(self, gesture, dx, _dy):
        ok, x0, _y0 = gesture.get_start_point()
        if ok:
            self._seek_x(x0 + dx)

    def toggle(self):
        if self.media:
            self.media.pause() if self.media.get_playing() else self.media.play()

    def restart(self):
        if self.media:
            self.media.seek(0)
            self.media.play()

    def stop(self):
        if self.media:
            self.media.pause()
            self.media.seek(0)
            self._tick()


# --------------------------------------------------------------------------- finestra

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app, path=None):
        super().__init__(application=app, default_width=1150, default_height=780)
        self.path = None
        self.dirty = False
        self._loading = False
        self._refresh_id = 0
        self.sel = 0
        self.focused_bar = None
        self.song = sf.new_song()

        self.toasts = Adw.ToastOverlay()
        self.stack = Adw.ViewStack()
        self.toasts.set_child(self.stack)
        self.stack.add_titled_with_icon(self._build_song_page(), "song", "Brano", "document-properties-symbolic")
        self.stack.add_titled_with_icon(self._build_sections_page(), "sections", "Sezioni", "view-list-symbolic")
        self.stack.add_titled_with_icon(self._build_arrangement_page(), "arr", "Arrangiamento",
                                        "media-playlist-repeat-symbolic")
        self.stack.add_titled_with_icon(self._build_yaml_page(), "yaml", "YAML", "text-x-generic-symbolic")

        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)
        logo = Gtk.Image.new_from_icon_name(APP_ID)
        logo.set_pixel_size(28)
        header.pack_start(logo)
        header.pack_start(icon_button("document-open-symbolic", "Apri (Ctrl+O)", self.action_open))
        header.pack_start(icon_button("document-save-symbolic", "Salva (Ctrl+S)", self.action_save))
        self.render_btn = Gtk.Button(tooltip_text="Genera l'audio e ascoltalo (Ctrl+R)")
        self.render_btn.set_child(Adw.ButtonContent(icon_name="media-playback-start-symbolic", label="Genera e ascolta"))
        self.render_btn.add_css_class("suggested-action")
        self.render_btn.add_css_class("render-btn")
        self.render_btn.connect("clicked", lambda _b: self.action_render())
        self.spinner = Gtk.Spinner()
        header.pack_end(self.render_btn)
        header.pack_end(self.spinner)

        self.banner = Adw.Banner(button_label="Installa")
        self.banner.connect("button-clicked", lambda _b: self.install_packs())

        view = Adw.ToolbarView()
        view.add_top_bar(Gtk.PopoverMenuBar.new_from_model(build_menu()))
        view.add_top_bar(header)
        view.add_top_bar(self.banner)
        view.set_content(self.toasts)
        view.add_bottom_bar(self._build_bottom_bar())
        self.set_content(view)
        self.connect("close-request", self._on_close)
        keys = Gtk.EventControllerKey(propagation_phase=Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self._on_key)
        self.add_controller(keys)
        bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 820sp"))
        bp.add_setter(self.split, "collapsed", True)
        bp.add_setter(self.editor_box, "orientation", Gtk.Orientation.VERTICAL)
        bp.add_setter(switcher, "policy", Adw.ViewSwitcherPolicy.NARROW)
        bp.add_setter(self.render_btn.get_child(), "label", "Genera")
        self.add_breakpoint(bp)

        self.check_packs()
        if path:
            self.load_file(path)
        else:
            self.load_song(self.song)
            GLib.idle_add(self.offer_draft)

    # ------------------------------------------------------------------ pagina Brano
    def _build_song_page(self):
        page = Adw.PreferencesPage()
        g = Adw.PreferencesGroup(title="🎵 Brano")
        self.w_title = Adw.EntryRow(title="Titolo")
        self.w_tempo = spin_row("Tempo", 30, 320, 1, subtitle="battiti al minuto (BPM)")
        self.w_groove = GrooveRow("Groove")
        self.w_transpose = spin_row("Trasposizione", -12, 12, 1, subtitle="semitoni: -1 per accordatura mezzo tono sotto")
        self.w_swing = Adw.ExpanderRow(title="Swing personalizzato", subtitle="se spento, lo decide il groove")
        self.w_swing.set_show_enable_switch(True)
        self.w_swing_val = spin_row("Swing", 0, 1, 0.05, 2, subtitle=SWING_HINT)
        self.w_swing.add_row(self.w_swing_val)
        for w, e in ((self.w_title, "✏️"), (self.w_tempo, "⏱️"), (self.w_groove, "🥁"), (self.w_transpose, "🎹"),
                     (self.w_swing, "🌀")):
            g.add(deco(w, e))
        page.add(g)

        g = Adw.PreferencesGroup(title="🔊 Suono")
        self.w_guitar = ChoiceRow("Chitarra", [("Gretsch", "Anniversary hollowbody, twang e calore"),
                                               ("Epiphone", "solid body (serve: backingtrack setup epiphone)")])
        self.w_amp = ChoiceRow("Ampli", [("auto", "quello del groove"), ("clean", "pulito"),
                                         ("blues", "leggermente sporco, caldo"), ("twang", "brillante, anni '50"),
                                         ("crunch", "distorsione media"), ("high", "distorsione pesante")],
                               "auto = quello del groove")
        self.w_double = ChoiceRow("Chitarra doppiata L/R", [("auto", "decide il groove"), ("sì", "due chitarre ai lati"),
                                                            ("no", "una chitarra al centro")], "due chitarre ai lati")
        self.w_slap = ChoiceRow("Slapback", [("auto", "decide il groove"), ("sì", "eco corta anni '50"),
                                             ("no", "niente eco")], "eco corta anni '50")
        self.w_bass = Adw.SwitchRow(title="Contrabbasso", subtitle="richiede il pacchetto 'bass'")
        for w, e in ((self.w_guitar, "🎸"), (self.w_amp, "📢"), (self.w_double, "👯"), (self.w_slap, "📣"),
                     (self.w_bass, "🎻")):
            g.add(deco(w, e))
        page.add(g)

        g = Adw.PreferencesGroup(title="🧱 Struttura")
        self.w_count = Adw.SwitchRow(title="Conteggio iniziale", subtitle="una battuta di bacchette")
        self.w_ending = Adw.SwitchRow(title="Finale", subtitle="accordo lungo con piatto")
        self.w_end_chord = Adw.EntryRow(title="Accordo finale (vuoto = primo accordo)")
        self.w_fills = Adw.SwitchRow(title="Rullate", subtitle="sull'ultima battuta di ogni sezione")
        self.w_crash = Adw.SwitchRow(title="Piatto sugli attacchi", subtitle="all'inizio di ogni sezione")
        for w, e in ((self.w_count, "🥢"), (self.w_ending, "🏁"), (self.w_end_chord, "🎯"), (self.w_fills, "🥁"),
                     (self.w_crash, "💥")):
            g.add(deco(w, e))
        page.add(g)

        g = Adw.PreferencesGroup(title="🧑‍🎤 Esecuzione")
        self.w_humanize = spin_row("Umanizzazione", 0, 2, 0.1, 1, "0 = a tempo perfetto, 2 = molto sciolto")
        self.w_strum = spin_row("Velocità pennata", 0, 40, 1, 0, "millisecondi tra una corda e l'altra")
        self.w_seed = spin_row("Variazione", 1, 9999, 1, 0, "cambia per altre dinamiche e round robin")
        for w, e in ((self.w_humanize, "🫀"), (self.w_strum, "🖐️"), (self.w_seed, "🎲")):
            g.add(deco(w, e))
        page.add(g)

        g = Adw.PreferencesGroup(title="💾 Output")
        self.w_outdir = Adw.EntryRow(title="Cartella di output")
        self.w_outdir.set_text("out")
        self.w_mp3 = Adw.SwitchRow(title="Crea anche l'MP3")
        self.w_stems = Adw.SwitchRow(title="Salva le tracce separate (stems)")
        for w, e in ((self.w_outdir, "📁"), (self.w_mp3, "🎧"), (self.w_stems, "🎚️")):
            g.add(deco(w, e))
        page.add(g)

        for w in (self.w_title, self.w_end_chord):
            w.connect("changed", self._song_changed)
        for w in (self.w_tempo, self.w_transpose, self.w_swing_val, self.w_humanize, self.w_strum, self.w_seed):
            w.connect("notify::value", self._song_changed)
        for w in (self.w_groove, self.w_guitar, self.w_amp, self.w_double, self.w_slap):
            w.connect("notify::selected", self._song_changed)
        for w in (self.w_bass, self.w_count, self.w_ending, self.w_fills, self.w_crash):
            w.connect("notify::active", self._song_changed)
        self.w_swing.connect("notify::enable-expansion", self._song_changed)
        return page

    def _song_changed(self, *_a):
        if self._loading:
            return
        s = self.song
        s["title"] = self.w_title.get_text().strip() or "Senza titolo"
        s["tempo"] = int(self.w_tempo.get_value())
        s["groove"] = GROOVE_NAMES[self.w_groove.get_selected()]
        self.s_groove.refresh_inherited()
        s["transpose"] = int(self.w_transpose.get_value())
        s["swing"] = round(self.w_swing_val.get_value(), 2) if self.w_swing.get_enable_expansion() else None
        s["guitar"] = sf.GUITARS[self.w_guitar.get_selected()]
        a = self.w_amp.get_selected()
        s["amp"] = sf.AMPS[a - 1] if a else None
        s["double"] = TRI_VAL[self.w_double.get_selected()]
        s["slapback"] = TRI_VAL[self.w_slap.get_selected()]
        s["bass"] = self.w_bass.get_active()
        s["count_in"] = self.w_count.get_active()
        s["ending"] = self.w_ending.get_active()
        s["ending_chord"] = self.w_end_chord.get_text().strip() or None
        s["fills"] = self.w_fills.get_active()
        s["crash"] = self.w_crash.get_active()
        s["humanize"] = round(self.w_humanize.get_value(), 1)
        s["strum_ms"] = int(self.w_strum.get_value())
        s["seed"] = int(self.w_seed.get_value())
        err = sf.check_chord(s["ending_chord"]) if s["ending_chord"] else None
        (self.w_end_chord.add_css_class if err else self.w_end_chord.remove_css_class)("error")
        self.changed()

    # ------------------------------------------------------------------ pagina Sezioni
    def _build_sections_page(self):
        self.split = Adw.OverlaySplitView(min_sidebar_width=220, max_sidebar_width=300, sidebar_width_fraction=0.28)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sec_list = Gtk.ListBox()
        self.sec_list.add_css_class("navigation-sidebar")
        self.sec_list.connect("row-selected", self._section_selected)
        sc = Gtk.ScrolledWindow(vexpand=True, child=self.sec_list)
        side.append(sc)
        bar = Gtk.Box(spacing=2, margin_start=6, margin_end=6, margin_top=6)
        bar.append(labeled_button("list-add-symbolic", "Nuova", "Nuova sezione (Ctrl+T)", self.add_section))
        bar.append(labeled_button("edit-copy-symbolic", "Duplica", "Duplica sezione (Ctrl+D)", self.duplicate_section))
        side.append(bar)
        bar = Gtk.Box(spacing=2, margin_start=6, margin_end=6, margin_bottom=6)
        bar.append(icon_button("go-up-symbolic", "Sposta su", self.move_section, -1))
        bar.append(icon_button("go-down-symbolic", "Sposta giù", self.move_section, 1))
        bar.append(Gtk.Box(hexpand=True))
        delete = labeled_button("user-trash-symbolic", "Elimina", "Elimina sezione", self.delete_section)
        delete.add_css_class("error")
        bar.append(delete)
        side.append(bar)
        self.split.set_sidebar(side)

        page = Adw.PreferencesPage()
        g = Adw.PreferencesGroup(title="🧩 Sezione")
        self.s_name = Adw.EntryRow(title="Nome")
        self.s_repeat = spin_row("Ripetizioni", 1, 64, 1, subtitle="quante volte suonare questa sezione")
        self.s_groove = GrooveRow("Groove", inherit=True, song_groove=lambda: self.song.get("groove"))
        self.s_volume = spin_row("Dinamica", 0.2, 1.5, 0.05, 2, "1 = normale, 0.8 = più piano")
        self.s_swing = Adw.ExpanderRow(title="Swing della sezione")
        self.s_swing.set_show_enable_switch(True)
        self.s_swing_val = spin_row("Swing", 0, 1, 0.05, 2, subtitle=SWING_HINT)
        self.s_swing.add_row(self.s_swing_val)
        self.s_fill = ChoiceRow("Rullata finale", [("auto", "come il brano"), ("sì", "rullata a fine sezione"),
                                                   ("no", "niente rullata")], "auto = come il brano")
        self.s_guitar = Adw.SwitchRow(title="Chitarra")
        self.s_drums = Adw.SwitchRow(title="Batteria")
        for w, e in ((self.s_name, "🏷️"), (self.s_repeat, "🔁"), (self.s_groove, "🥁"), (self.s_volume, "🔉"),
                     (self.s_swing, "🌀"), (self.s_fill, "🥁"), (self.s_guitar, "🎸"), (self.s_drums, "🪘")):
            g.add(deco(w, e))
        page.add(g)

        chords = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_start=18, margin_end=18,
                         margin_top=14, margin_bottom=18)
        head = Gtk.Box(spacing=8)
        title = Gtk.Label(label="🎼 Accordi", xalign=0)
        title.add_css_class("title-2")
        head.append(title)
        self.bars_info = Gtk.Label(xalign=1, hexpand=True)
        self.bars_info.add_css_class("dim-label")
        head.append(self.bars_info)
        chords.append(head)
        hint = Gtk.Label(wrap=True, xalign=0,
                         label="Una casella = una battuta di 4 tempi. Più accordi si dividono i tempi in parti uguali; "
                               "'.' prolunga l'accordo prima: 'Em . D C' = Em 2 tempi, D 1, C 1. "
                               "'%' ripete la battuta precedente, 'N.C.' = pausa. Invio = battuta successiva.")
        hint.add_css_class("dim-label")
        hint.add_css_class("caption")
        chords.append(hint)
        tools = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tools.add_css_class("card")
        tools.add_css_class("builder")
        builder = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=8,
                              column_spacing=6, row_spacing=6, homogeneous=False)
        self.c_root = GridPicker(sf.ROOTS, note_rows(sf.ROOTS), fmt=lambda i: "Tonica: " + sf.ROOTS[i])
        self.c_root.set_selected(sf.ROOTS.index("A"))
        self.c_root.set_tooltip_text("Tonica")
        qual_labels = [suf or "maggiore" for suf, _d in sf.QUALITY_CHOICES]
        self.c_qual = GridPicker(qual_labels, [list(range(i, min(i + 4, len(qual_labels))))
                                               for i in range(0, len(qual_labels), 4)],
                                 tooltips=[d for _s, d in sf.QUALITY_CHOICES],
                                 fmt=lambda i: "Tipo: %s" % sf.QUALITY_CHOICES[i][1])
        self.c_qual.set_tooltip_text("Tipo di accordo")
        bass_labels = ["tonica"] + ["/" + r for r in sf.ROOTS]
        self.c_bass = GridPicker(bass_labels, [[0]] + note_rows(sf.ROOTS, offset=1), columns_hint=7,
                                 fmt=lambda i: "Basso: " + ("tonica" if i == 0 else sf.ROOTS[i - 1]))
        self.c_bass.set_tooltip_text("Basso diverso dalla tonica (accordo slash, es. D/F#)")
        self.c_preview = Gtk.Label(width_chars=7)
        self.c_preview.add_css_class("title-4")
        for dd in (self.c_root, self.c_qual, self.c_bass):
            dd.connect("notify::selected", lambda *_: (self.c_preview.set_label(self.built_chord()),
                                                       self.rebuild_palette()))
            builder.append(dd)
        self.c_preview.set_tooltip_text("Trascina l'accordo su una battuta")
        self.c_preview.add_css_class("chip")
        self.c_preview.add_css_class("chip-main")
        drag_source(self.c_preview, lambda: "chord:" + self.built_chord())
        builder.append(self.c_preview)
        add_new = Gtk.Button(label="Nuova battuta")
        add_new.add_css_class("suggested-action")
        add_new.connect("clicked", lambda _b: self.add_bar(self.built_chord()))
        add_in = Gtk.Button(label="Aggiungi alla battuta", tooltip_text="Aggiunge l'accordo alla battuta selezionata")
        add_in.connect("clicked", lambda _b: self.append_to_focused(self.built_chord()))
        builder.append(add_new)
        builder.append(add_in)
        tools.append(builder)
        quick = Gtk.Box(spacing=6)
        dup = labeled_button("edit-copy-symbolic", "Duplica battuta", "Duplica la battuta selezionata (Ctrl+Shift+D)",
                             self.duplicate_focused_bar)
        dup.remove_css_class("flat")
        quick.append(dup)
        for label, tok, tip in (("+ %", "%", "ripeti la battuta precedente"), ("+ N.C.", "N.C.", "battuta senza chitarra"),
                                ("+ vuota", "", "battuta da riempire")):
            b = Gtk.Button(label=label, tooltip_text=tip)
            b.connect("clicked", lambda _b, t=tok: self.add_bar(t))
            quick.append(b)
        quick.append(Gtk.Box(hexpand=True))
        clear = Gtk.Button(label="Svuota")
        clear.add_css_class("destructive-action")
        clear.connect("clicked", lambda _b: self.set_bars([]))
        quick.append(clear)
        tools.append(quick)
        chords.append(tools)
        pal = Gtk.Box(spacing=8)
        pal_label = Gtk.Label(label="🎨 Tavolozza")
        pal_label.add_css_class("heading")
        pal_label.set_tooltip_text("Trascina un accordo su una battuta per metterlo lì; clic = nuova battuta")
        pal.append(pal_label)
        self.palette = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=20,
                                   column_spacing=4, row_spacing=4, hexpand=True)
        pal.append(self.palette)
        chords.append(pal)
        self.flow = Gtk.FlowBox(max_children_per_line=4, min_children_per_line=2, homogeneous=True,
                                selection_mode=Gtk.SelectionMode.NONE, column_spacing=4, row_spacing=4,
                                valign=Gtk.Align.START)
        self.flow.add_css_class("bar-grid")
        chords.append(self.flow)
        self.c_preview.set_label(self.built_chord())

        g = Adw.PreferencesGroup(title="✨ Modelli di giro", description="Riempie la sezione con un giro classico.")
        self.t_name = deco(MenuRow("Modello", list(sf.TEMPLATES), TEMPLATE_GROUPS, button_label=lambda n: n,
                                   item_label=lambda n: n), "📜")
        self.t_key_sub = lambda *_: self.t_name.set_tooltip_text("| " + " | ".join(
            sf.template_bars(list(sf.TEMPLATES)[self.t_name.get_selected()], sf.KEYS[self.t_key.get_selected()])) + " |")
        self.t_name.connect("notify::selected", self.t_key_sub)
        self.t_key = deco(PickerRow("Tonalità", GridPicker(sf.KEYS, note_rows(sf.KEYS))), "🔑")
        self.t_key.set_selected(sf.KEYS.index("A"))
        self.t_key.connect("notify::selected", self.t_key_sub)
        self.t_key_sub()
        buttons = Gtk.Box(spacing=6, halign=Gtk.Align.END, margin_top=8)
        rep = Gtk.Button(label="Sostituisci accordi")
        rep.connect("clicked", lambda _b: self.apply_template(replace=True))
        app = Gtk.Button(label="Aggiungi in coda")
        app.connect("clicked", lambda _b: self.apply_template(replace=False))
        buttons.append(app)
        buttons.append(rep)
        g.add(self.t_name)
        g.add(self.t_key)
        g.add(buttons)
        page.add(g)
        empty = Adw.StatusPage(title="Nessuna sezione", icon_name="view-list-symbolic",
                               description="Una sezione è un pezzo del brano (intro, strofa, ritornello…) "
                                           "che puoi ripetere quante volte vuoi.")
        start = Gtk.Button(label="🎸  Aggiungi la prima sezione", halign=Gtk.Align.CENTER)
        start.add_css_class("suggested-action")
        start.add_css_class("pill")
        start.connect("clicked", lambda _b: self.add_section())
        empty.set_child(start)
        self.sec_stack = Gtk.Stack()
        # due colonne affiancate: accordi (larga) | impostazioni della sezione e modelli
        page.set_size_request(440, -1)
        chords_scroll = Gtk.ScrolledWindow(child=chords, hexpand=True, vexpand=True,
                                           hscrollbar_policy=Gtk.PolicyType.NEVER)
        chords_scroll.set_min_content_height(320)  # a finestra stretta gli accordi restano in primo piano
        # divisore trascinabile: lo spazio in più va agli accordi, le impostazioni restano almeno 440 px
        self.editor_box = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=True,
                                    start_child=chords_scroll, end_child=page,
                                    resize_start_child=True, resize_end_child=False,
                                    shrink_start_child=False, shrink_end_child=False)
        self.sec_stack.add_named(self.editor_box, "editor")
        self.sec_stack.add_named(empty, "empty")
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        toggle = Gtk.ToggleButton(halign=Gtk.Align.START, margin_start=8, margin_top=6,
                                  tooltip_text="Mostra l'elenco delle sezioni")
        toggle.set_child(Adw.ButtonContent(icon_name="sidebar-show-symbolic", label="Sezioni"))
        self.split.bind_property("collapsed", toggle, "visible", GObject.BindingFlags.SYNC_CREATE)
        toggle.bind_property("active", self.split, "show-sidebar",
                             GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE)
        content.append(toggle)
        self.sec_stack.set_vexpand(True)
        content.append(self.sec_stack)
        self.split.set_content(content)

        self.s_name.connect("changed", self._section_changed)
        for w in (self.s_repeat, self.s_volume, self.s_swing_val):
            w.connect("notify::value", self._section_changed)
        for w in (self.s_groove, self.s_fill):
            w.connect("notify::selected", self._section_changed)
        for w in (self.s_guitar, self.s_drums):
            w.connect("notify::active", self._section_changed)
        self.s_swing.connect("notify::enable-expansion", self._section_changed)
        return self.split

    def built_chord(self):
        root = sf.ROOTS[self.c_root.get_selected()]
        suf = sf.QUALITY_CHOICES[self.c_qual.get_selected()][0]
        b = self.c_bass.get_selected()
        return root + suf + ("/" + sf.ROOTS[b - 1] if b else "")

    @property
    def section(self):
        secs = self.song["sections"]
        return secs[self.sel] if 0 <= self.sel < len(secs) else None

    def refresh_section_list(self, select=None):
        self._loading = True
        self.sec_list.remove_all()
        for i, sec in enumerate(self.song["sections"]):
            row = Adw.ActionRow(title=GLib.markup_escape_text(sec["name"] or "(senza nome)"))
            row.set_subtitle(self._section_subtitle(sec))
            dot = Gtk.Label(label="●")
            dot.add_css_class("dot")
            dot.add_css_class("sec-%d" % (i % len(SECTION_COLORS)))
            row.add_prefix(dot)
            row.emoji = Gtk.Label(label=style_emoji(sec["groove"] or self.song["groove"]))
            row.emoji.add_css_class("emoji")
            row.add_suffix(row.emoji)
            self.sec_list.append(row)
        self._loading = False
        if select is not None:
            self.sel = max(0, min(select, len(self.song["sections"]) - 1))
        row = self.sec_list.get_row_at_index(self.sel)
        if row:
            self.sec_list.select_row(row)
        else:
            self.load_section()

    def _section_subtitle(self, sec):
        bad = sum(1 for j, b in enumerate(sec["bars"]) if sf.check_bar(b, j == 0))
        parts = ["x%d" % sec["repeat"], "%d battute" % len(sec["bars"]), sec["groove"] or "groove del brano"]
        if bad:
            parts.append("⚠ %d da correggere" % bad)
        return GLib.markup_escape_text(" · ".join(parts))

    def update_section_rows(self):
        sec = self.section
        if sec is not None and hasattr(self, "bars_info"):
            n = len(sec["bars"])
            self.bars_info.set_label("%s · %d battut%s × %d" % (sec["name"] or "—", n, "a" if n == 1 else "e",
                                                               sec["repeat"]))
        for i, sec in enumerate(self.song["sections"]):
            row = self.sec_list.get_row_at_index(i)
            if row:
                row.set_title(GLib.markup_escape_text(sec["name"] or "(senza nome)"))
                row.set_subtitle(self._section_subtitle(sec))
                row.emoji.set_label(style_emoji(sec["groove"] or self.song["groove"]))

    def _section_selected(self, _lb, row):
        if self._loading or row is None:
            return
        self.sel = row.get_index()
        self.load_section()
        if self.split.get_collapsed():
            self.split.set_show_sidebar(False)

    def load_section(self):
        sec = self.section
        self.sec_stack.set_visible_child_name("editor" if sec else "empty")
        self._loading = True
        editable = sec is not None
        for w in (self.s_name, self.s_repeat, self.s_groove, self.s_volume, self.s_swing, self.s_fill,
                  self.s_guitar, self.s_drums, self.flow):
            w.set_sensitive(editable)
        if sec:
            self.s_name.set_text(sec["name"])
            self.s_repeat.set_value(sec["repeat"])
            self.s_groove.set_selected(GROOVE_NAMES.index(sec["groove"]) + 1 if sec["groove"] in GROOVES else 0)
            self.s_volume.set_value(sec["volume"])
            self.s_swing.set_enable_expansion(sec["swing"] is not None)
            self.s_swing_val.set_value(sec["swing"] if sec["swing"] is not None else 0.5)
            self.s_fill.set_selected({None: 0, True: 1, False: 2}.get(sec["fill"], 0))
            self.s_guitar.set_active(bool(sec["guitar"]))
            self.s_drums.set_active(bool(sec["drums"]))
        self._loading = False
        self.rebuild_bars()

    def _section_changed(self, *_a):
        sec = self.section
        if self._loading or sec is None:
            return
        sec["name"] = self.s_name.get_text().strip()
        sec["repeat"] = int(self.s_repeat.get_value())
        g = self.s_groove.get_selected()
        sec["groove"] = GROOVE_NAMES[g - 1] if g else None
        sec["volume"] = round(self.s_volume.get_value(), 2)
        sec["swing"] = round(self.s_swing_val.get_value(), 2) if self.s_swing.get_enable_expansion() else None
        sec["fill"] = [None, True, False][self.s_fill.get_selected()]
        sec["guitar"] = self.s_guitar.get_active()
        sec["drums"] = self.s_drums.get_active()
        dup = [s["name"] for s in self.song["sections"]].count(sec["name"]) > 1
        (self.s_name.add_css_class if (dup or not sec["name"]) else self.s_name.remove_css_class)("error")
        self.update_section_rows()
        self.rebuild_arrangement()
        self.changed()

    def _unique_name(self, base):
        names = {s["name"] for s in self.song["sections"]}
        if base not in names:
            return base
        n = 2
        while "%s %d" % (base, n) in names:
            n += 1
        return "%s %d" % (base, n)

    def add_section(self):
        sec = dict(sf.SECTION_DEFAULTS, name=self._unique_name("Sezione"), bars=[])
        self.song["sections"].append(sec)
        self.refresh_section_list(select=len(self.song["sections"]) - 1)
        self.changed()

    def duplicate_section(self):
        sec = self.section
        if not sec:
            return
        copy = dict(sec, bars=list(sec["bars"]), name=self._unique_name(sec["name"]))
        self.song["sections"].insert(self.sel + 1, copy)
        self.refresh_section_list(select=self.sel + 1)
        self.changed()

    def move_section(self, delta):
        secs, i = self.song["sections"], self.sel
        j = i + delta
        if 0 <= i < len(secs) and 0 <= j < len(secs):
            secs[i], secs[j] = secs[j], secs[i]
            self.refresh_section_list(select=j)
            self.changed()

    def delete_section(self):
        sec = self.section
        if not sec:
            return
        self.song["sections"].pop(self.sel)
        self.song["arrangement"] = [a for a in self.song["arrangement"] if a["section"] != sec["name"]]
        self.refresh_section_list(select=self.sel)
        self.rebuild_arrangement()
        self.toast("Sezione '%s' eliminata" % sec["name"])
        self.changed()

    # battute ----------------------------------------------------------------
    def rebuild_bars(self, focus=None):
        self.flow.remove_all()
        self.cards = []
        sec = self.section
        if not sec:
            return
        n = len(sec["bars"])
        self.bars_info.set_label("%s · %d battut%s × %d" % (sec["name"] or "—", n, "a" if n == 1 else "e", sec["repeat"]))
        color = self.sel % len(SECTION_COLORS)
        for i, text in enumerate(sec["bars"]):
            card = BarCell(self, i, text, color)
            self.cards.append(card)
            self.flow.append(card)
        plus = Gtk.Button(label="＋", tooltip_text="Nuova battuta (Ctrl+B) — puoi anche trascinarci un accordo")
        plus.add_css_class("bar-add")
        plus.connect("clicked", lambda _b: self.add_bar(""))
        drop_target(plus, lambda value: self.drop_on_bar(len(self.section["bars"]), value))
        self.flow.append(plus)
        self.rebuild_palette()
        if focus is not None and 0 <= focus < len(self.cards):
            self.cards[focus].entry.grab_focus()
            self.focused_bar = focus

    def rebuild_palette(self):
        """Accordi trascinabili: quello costruito + quelli già usati nel brano."""
        if not hasattr(self, "palette"):
            return
        self.palette.remove_all()
        seen = []
        for sec in self.song["sections"]:
            for bar in sec["bars"]:
                for tok in bar.split():
                    if tok not in (".", "-", "/", "%") and tok.upper() not in ("N.C.", "NC") \
                            and not sf.check_chord(tok) and tok not in seen:
                        seen.append(tok)
        for tok in seen[:24]:
            chip = Gtk.Button(label=tok, tooltip_text="Clic: nuova battuta · trascina su una battuta")
            chip.add_css_class("chip")
            chip.connect("clicked", lambda _b, t=tok: self.add_bar(t))
            drag_source(chip, lambda t=tok: "chord:" + t)
            self.palette.append(chip)

    def drop_on_bar(self, index, value):
        """Rilascio sulla battuta 'index': un accordo la sostituisce, una battuta trascinata si sposta lì."""
        sec = self.section
        if not sec or not isinstance(value, str):
            return False
        if value.startswith("chord:"):
            chord = value[6:]
            if index >= len(sec["bars"]):
                self.add_bar(chord)
            else:
                self.cards[index].entry.set_text(chord)
                self.toast("Battuta %d: %s" % (index + 1, chord))
            return True
        if value.startswith("bar:"):
            src = int(value[4:])
            if 0 <= src < len(sec["bars"]) and src != index:
                bar = sec["bars"].pop(src)
                sec["bars"].insert(min(index, len(sec["bars"])), bar)
                self.rebuild_bars(focus=min(index, len(sec["bars"]) - 1))
                self.update_section_rows()
                self.changed()
            return True
        return False

    def insert_bar(self, index):
        sec = self.section
        if sec:
            sec["bars"].insert(index, "")
            self.rebuild_bars(focus=index)
            self.update_section_rows()
            self.changed()

    def set_focused_bar(self, index):
        self.focused_bar = index

    def focus_bar(self, index, create=False):
        sec = self.section
        if index >= len(sec["bars"]) and create:
            self.add_bar("")
            return
        if 0 <= index < len(self.cards):
            self.cards[index].entry.grab_focus()

    def bar_changed(self, index, text):
        sec = self.section
        if sec and index < len(sec["bars"]):
            sec["bars"][index] = text.strip()
            if index == 0 and len(self.cards) > 1:
                self.cards[1].validate()
            self.update_section_rows()
            self.changed()

    def add_bar(self, text):
        sec = self.section
        if not sec:
            self.toast("Crea prima una sezione")
            return
        sec["bars"].append(text)
        self.rebuild_bars(focus=len(sec["bars"]) - 1)
        self.update_section_rows()
        self.changed()

    def append_to_focused(self, chord):
        sec = self.section
        i = self.focused_bar
        if not sec or i is None or i >= len(sec["bars"]):
            self.add_bar(chord)
            return
        text = (sec["bars"][i] + " " + chord).strip()
        if len(text.split()) > 4:
            self.toast("Massimo 4 accordi per battuta (uno per tempo)")
            return
        self.cards[i].entry.set_text(text)

    def duplicate_bar(self, index):
        sec = self.section
        if sec and 0 <= index < len(sec["bars"]):
            sec["bars"].insert(index + 1, sec["bars"][index])
            self.rebuild_bars(focus=index + 1)
            self.update_section_rows()
            self.changed()

    def duplicate_focused_bar(self):
        sec = self.section
        if not sec or not sec["bars"]:
            self.toast("Nessuna battuta da duplicare")
            return
        i = self.focused_bar if self.focused_bar is not None and self.focused_bar < len(sec["bars"]) else len(sec["bars"]) - 1
        self.duplicate_bar(i)

    def remove_bar(self, index):
        sec = self.section
        if sec and index < len(sec["bars"]):
            sec["bars"].pop(index)
            self.rebuild_bars(focus=min(index, len(sec["bars"]) - 1))
            self.update_section_rows()
            self.changed()

    def set_bars(self, bars):
        sec = self.section
        if sec is None:
            return
        sec["bars"] = list(bars)
        self.rebuild_bars()
        self.update_section_rows()
        self.changed()

    def apply_template(self, replace):
        if not self.section:
            self.add_section()
        bars = sf.template_bars(list(sf.TEMPLATES)[self.t_name.get_selected()], sf.KEYS[self.t_key.get_selected()])
        self.set_bars(bars if replace else self.section["bars"] + bars)

    # ------------------------------------------------------------------ pagina Arrangiamento
    def _build_arrangement_page(self):
        page = Adw.PreferencesPage()
        self.arr_group = Adw.PreferencesGroup(
            title="Ordine delle sezioni",
            description="Se la lista è vuota, le sezioni suonano nell'ordine della pagina Sezioni, "
                        "ognuna con le sue ripetizioni. 'x' = 0 usa le ripetizioni della sezione.")
        add = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Aggiungi al fondo")
        add.add_css_class("flat")
        add.connect("clicked", lambda _b: self.add_arrangement())
        self.arr_group.set_header_suffix(add)
        page.add(self.arr_group)
        g = Adw.PreferencesGroup(title="Riepilogo")
        self.summary_row = Adw.ActionRow(title="Durata")
        g.add(self.summary_row)
        page.add(g)
        self.arr_rows = []
        return page

    def rebuild_arrangement(self):
        for row in self.arr_rows:
            self.arr_group.remove(row)
        self.arr_rows = []
        names = [s["name"] for s in self.song["sections"]]
        if not self.song["arrangement"]:
            row = Adw.ActionRow(title="Ordine automatico",
                                subtitle=GLib.markup_escape_text(
                                    " → ".join("%s x%d" % (s["name"], s["repeat"]) for s in self.song["sections"])))
            self.arr_group.add(row)
            self.arr_rows.append(row)
            return
        for i, item in enumerate(self.song["arrangement"]):
            row = Adw.ActionRow(title="%d." % (i + 1))
            dd = GridPicker(names or ["—"], [[j] for j in range(len(names or ["—"]))])
            if item["section"] in names:
                dd.set_selected(names.index(item["section"]))
            dd.connect("notify::selected", self._arr_changed, i)
            spin = Gtk.SpinButton.new_with_range(0, 64, 1)
            spin.set_valign(Gtk.Align.CENTER)
            spin.set_value(item["repeat"] or 0)
            spin.set_tooltip_text("ripetizioni (0 = come la sezione)")
            spin.connect("value-changed", self._arr_changed, i)
            row.add_suffix(dd)
            row.add_suffix(Gtk.Label(label="x"))
            row.add_suffix(spin)
            row.add_suffix(icon_button("go-up-symbolic", "Su", self.move_arrangement, i, -1))
            row.add_suffix(icon_button("go-down-symbolic", "Giù", self.move_arrangement, i, 1))
            row.add_suffix(icon_button("user-trash-symbolic", "Rimuovi", self.remove_arrangement, i))
            if item["section"] not in names:
                row.set_subtitle("⚠ sezione '%s' inesistente" % GLib.markup_escape_text(item["section"]))
            self.arr_group.add(row)
            self.arr_rows.append(row)

    def _arr_changed(self, widget, *args):
        i = args[-1]
        names = [s["name"] for s in self.song["sections"]]
        item = self.song["arrangement"][i]
        if isinstance(widget, GridPicker):
            if names:
                item["section"] = names[widget.get_selected()]
        else:
            item["repeat"] = int(widget.get_value()) or None
        self.changed()

    def add_arrangement(self):
        if not self.song["sections"]:
            self.toast("Crea prima una sezione")
            return
        if not self.song["arrangement"]:  # parte dall'ordine automatico, così è facile modificarlo
            self.song["arrangement"] = [{"section": s["name"], "repeat": None} for s in self.song["sections"]]
        else:
            self.song["arrangement"].append({"section": self.song["sections"][0]["name"], "repeat": None})
        self.rebuild_arrangement()
        self.changed()

    def move_arrangement(self, i, delta):
        a = self.song["arrangement"]
        j = i + delta
        if 0 <= j < len(a):
            a[i], a[j] = a[j], a[i]
            self.rebuild_arrangement()
            self.changed()

    def remove_arrangement(self, i):
        self.song["arrangement"].pop(i)
        self.rebuild_arrangement()
        self.changed()

    # ------------------------------------------------------------------ pagina YAML
    def _build_yaml_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.yaml_view = Gtk.TextView(editable=False, monospace=True, vexpand=True)
        self.yaml_view.add_css_class("yaml-view")
        box.append(Gtk.ScrolledWindow(child=self.yaml_view, vexpand=True))
        copy = Gtk.Button(label="Copia", halign=Gtk.Align.END, margin_end=12, margin_bottom=12)
        copy.connect("clicked", lambda _b: (self.get_clipboard().set(sf.to_yaml(self.song)), self.toast("YAML copiato")))
        box.append(copy)
        return box

    # ------------------------------------------------------------------ barra inferiore
    def _build_bottom_bar(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.player = Player(self)
        outer.append(self.player)
        box = Gtk.Box(spacing=12)
        box.add_css_class("summary")
        self.status = Gtk.Label(xalign=0, hexpand=True, ellipsize=3)
        box.append(self.status)
        outer.append(box)
        return outer

    # ------------------------------------------------------------------ stato
    def load_song(self, song):
        self.song = song
        self._loading = True
        s = song
        self.w_title.set_text(s["title"] or "")
        self.w_tempo.set_value(s["tempo"] or 120)
        self.w_groove.set_selected(GROOVE_NAMES.index(s["groove"]) if s["groove"] in GROOVES else 0)
        self.w_transpose.set_value(s["transpose"] or 0)
        self.w_swing.set_enable_expansion(s["swing"] is not None)
        self.w_swing_val.set_value(s["swing"] if s["swing"] is not None else 0.5)
        self.w_guitar.set_selected(sf.GUITARS.index(s["guitar"]) if s["guitar"] in sf.GUITARS else 0)
        self.w_amp.set_selected(sf.AMPS.index(s["amp"]) + 1 if s["amp"] in sf.AMPS else 0)
        self.w_double.set_selected(TRI_VAL.index(s["double"]) if s["double"] in TRI_VAL else 0)
        self.w_slap.set_selected(TRI_VAL.index(s["slapback"]) if s["slapback"] in TRI_VAL else 0)
        self.w_bass.set_active(bool(s["bass"]))
        self.w_count.set_active(bool(s["count_in"]))
        self.w_ending.set_active(bool(s["ending"]))
        self.w_end_chord.set_text(s["ending_chord"] or "")
        self.w_fills.set_active(bool(s["fills"]))
        self.w_crash.set_active(bool(s["crash"]))
        self.w_humanize.set_value(s["humanize"])
        self.w_strum.set_value(s["strum_ms"])
        self.w_seed.set_value(s["seed"])
        self._loading = False
        self.sel = 0
        self.refresh_section_list(select=0)
        self.rebuild_arrangement()
        self.dirty = False
        self.refresh()

    def changed(self):
        if self._loading:
            return
        self.dirty = True
        if not self._refresh_id:
            self._refresh_id = GLib.timeout_add(200, self.refresh)

    def refresh(self):
        self._refresh_id = 0
        if self.dirty:
            self.save_draft()
        name = Path(self.path).name if self.path else "nuovo brano"
        self.set_title("%s%s — backingtrack" % ("• " if self.dirty else "", name))
        self.yaml_view.get_buffer().set_text(sf.to_yaml(self.song))
        errors = sf.validate(self.song)
        self.errors = errors
        self.status.remove_css_class("status-ok")
        self.status.remove_css_class("status-bad")
        self.status.add_css_class("status-bad" if errors else "status-ok")
        if errors:
            self.status.set_markup("<b>⚠ %d da correggere:</b> %s" % (
                len(errors), GLib.markup_escape_text(errors[0])))
            self.status.set_tooltip_text("\n".join(errors))
            self.summary_row.set_subtitle("—")
        else:
            try:
                order, timeline = build_timeline(sf.to_song_dict(self.song))
                bars = len(timeline) + (1 if self.song["count_in"] else 0) + (2 if self.song["ending"] else 0)
                secs = bars * 4 * 60 / self.song["tempo"]
                info = "%d battute · %d:%02d" % (len(timeline), secs // 60, secs % 60)
                self.summary_row.set_subtitle(info)
                self.status.set_markup("✓ Pronto · " + info + (" · non salvato (puoi generare lo stesso)"
                                                                if self.dirty else ""))
                self.status.set_tooltip_text(None)
            except SongError as e:
                self.status.set_text("⚠ %s" % e)
        self.render_btn.set_sensitive(not errors and not self.spinner.get_spinning())
        return False

    def toast(self, text):
        self.toasts.add_toast(Adw.Toast(title=GLib.markup_escape_text(text), timeout=3))

    def alert(self, heading, body):
        d = Adw.AlertDialog(heading=heading, body=body)
        d.add_response("ok", "OK")
        d.present(self)

    # ------------------------------------------------------------------ file
    def _filters(self):
        f = Gtk.FileFilter()
        f.set_name("Canzoni YAML")
        f.add_pattern("*.yaml")
        f.add_pattern("*.yml")
        store = Gio.ListStore.new(Gtk.FileFilter)
        store.append(f)
        return store

    # bozza automatica ------------------------------------------------------
    def save_draft(self):
        """Copia di sicurezza del brano a ogni modifica: sopravvive a chiusure e crash."""
        import json
        try:
            DRAFT.parent.mkdir(parents=True, exist_ok=True)
            DRAFT.write_text(json.dumps({"path": self.path, "yaml": sf.to_yaml(self.song),
                                         "time": GLib.DateTime.new_now_local().format("%d/%m %H:%M")}),
                             encoding="utf-8")
        except OSError:
            pass

    def drop_draft(self):
        try:
            DRAFT.unlink()
        except OSError:
            pass

    def offer_draft(self):
        import json
        try:
            draft = json.loads(DRAFT.read_text(encoding="utf-8"))
            data = sf.from_song_dict(__import__("yaml").safe_load(draft["yaml"]))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return False
        name = Path(draft["path"]).name if draft.get("path") else data["title"]
        d = Adw.AlertDialog(heading="Ripristinare le modifiche non salvate?",
                            body="C'è una bozza di «%s» del %s che non era stata salvata." % (name, draft.get("time", "?")))
        d.add_response("discard", "Scarta")
        d.add_response("restore", "Ripristina")
        d.set_response_appearance("restore", Adw.ResponseAppearance.SUGGESTED)
        d.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        d.set_default_response("restore")

        def on_response(_d, resp):
            if resp == "restore":
                self.path = draft.get("path")
                self.load_song(data)
                self.dirty = True
                self.refresh()
                self.toast("Bozza ripristinata: ricordati di salvare (Ctrl+S)")
            else:
                self.drop_draft()
        d.connect("response", on_response)
        d.present(self)
        return False

    def confirm_discard(self, then):
        if not self.dirty:
            then()
            return
        d = Adw.AlertDialog(heading="Modifiche non salvate",
                            body="Il brano ha modifiche non salvate. Vuoi salvarle?")
        d.add_response("cancel", "Annulla")
        d.add_response("discard", "Non salvare")
        d.add_response("save", "Salva")
        d.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        d.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        d.set_default_response("save")

        def on_response(_d, resp):
            if resp == "discard":
                self.drop_draft()
                then()
            elif resp == "save":
                self.action_save(after=then)

        d.connect("response", on_response)
        d.present(self)

    def action_new(self):
        def do():
            self.path = None
            self.load_song(sf.new_song())
            self.stack.set_visible_child_name("song")
        self.confirm_discard(do)

    def action_open(self):
        def pick():
            dlg = Gtk.FileDialog(title="Apri canzone", filters=self._filters())
            examples = Path(__file__).resolve().parent.parent / "examples"
            if examples.is_dir():
                dlg.set_initial_folder(Gio.File.new_for_path(str(examples)))

            def done(d, res):
                try:
                    f = d.open_finish(res)
                except GLib.Error:
                    return
                self.load_file(f.get_path())
            dlg.open(self, None, done)
        self.confirm_discard(pick)

    def load_file(self, path):
        try:
            self.path = str(path)
            song = sf.from_song_dict(load_song(path))
            song["header"] = sf.header_comments(Path(path).read_text(encoding="utf-8"))
            self.load_song(song)
            self.toast("Aperto %s" % Path(path).name)
        except SongError as e:
            self.path = None
            self.alert("Impossibile aprire il file", str(e))

    def action_save(self, after=None):
        if not self.path:
            self.action_save_as(after)
            return
        try:
            Path(self.path).write_text(sf.to_yaml(self.song), encoding="utf-8")
        except OSError as e:
            self.alert("Salvataggio non riuscito", str(e))
            return
        self.dirty = False
        self.drop_draft()
        self.refresh()
        self.toast("Salvato %s" % Path(self.path).name)
        if after:
            after()

    def action_save_as(self, after=None):
        dlg = Gtk.FileDialog(title="Salva canzone", filters=self._filters())
        dlg.set_initial_name(slug(self.song["title"]) + ".yaml")

        def done(d, res):
            try:
                f = d.save_finish(res)
            except GLib.Error:
                return
            path = f.get_path()
            if not path.endswith((".yaml", ".yml")):
                path += ".yaml"
            self.path = path
            self.action_save(after)
        dlg.save(self, None, done)

    def _on_close(self, _w):
        if not self.dirty:
            self.drop_draft()
            return False
        self.confirm_discard(self.destroy)
        return True

    # ------------------------------------------------------------------ campioni
    def required_packs(self):
        need = [self.song.get("guitar") or "gretsch", "drums", "cabs"]
        if self.song.get("bass"):
            need.append("bass")
        return [p for p in need if not packs.is_installed(p)]

    def check_packs(self):
        missing = self.required_packs()
        if missing:
            mb = sum(packs.PACKS[p].get("light_mb", packs.PACKS[p]["size_mb"]) for p in missing)
            self.banner.set_title("Mancano i campioni: %s (~%d MB, una volta sola)" % (", ".join(missing), mb))
        self.banner.set_revealed(bool(missing))
        return missing

    def install_packs(self):
        missing = self.required_packs()
        if not missing:
            return
        self.banner.set_title("Scarico i campioni… (%s)" % ", ".join(missing))
        self.banner.set_button_label(None)
        self.spinner.start()

        def work():
            try:
                for p in missing:
                    packs.install(p)
                GLib.idle_add(done, None)
            except Exception as e:  # noqa: BLE001 — mostrato all'utente
                GLib.idle_add(done, str(e))

        def done(err):
            self.spinner.stop()
            self.banner.set_button_label("Installa")
            if err:
                self.alert("Download non riuscito", err)
            else:
                self.toast("Campioni installati")
            self.check_packs()
            self.refresh()
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------------ render e ascolto
    def action_render(self):
        self.refresh()
        if self.errors:
            self.stack.set_visible_child_name("sections")
            self.alert("Il brano ha errori", "\n".join(self.errors[:10]))
            return
        if self.check_packs():
            self.alert("Campioni mancanti", "Installa i campioni con il pulsante nella barra in alto.")
            return
        song = sf.to_song_dict(self.song)
        bars = song_bars(song, self.song["sections"])
        outdir = Path(self.w_outdir.get_text().strip() or "out").expanduser()
        out = outdir / slug(self.song["title"])
        mp3, stems = self.w_mp3.get_active(), self.w_stems.get_active()
        self.spinner.start()
        self.render_btn.set_sensitive(False)
        self.status.set_text("Genero %s…" % out.name)
        if self.player.media:
            self.player.media.pause()

        def work():
            from .cli import render
            try:
                result = render(song, out, mp3=mp3, stems=stems, log=lambda *_a: None)
                result["wave"] = make_waveform(result["wav"])
                GLib.idle_add(done, result, None)
            except SongError as e:
                GLib.idle_add(done, None, str(e))
            except Exception:  # noqa: BLE001
                GLib.idle_add(done, None, traceback.format_exc(limit=3))

        def done(result, err):
            self.spinner.stop()
            self.refresh()
            if err:
                self.alert("Generazione non riuscita", err)
                return
            self.last_output = result["wav"]
            self.player.load(result["wav"], self.song["title"], result.get("wave"), bars)
            self.status.set_text("✓ %s" % result["wav"])
            self.toast("Fatto! In riproduzione")
        threading.Thread(target=work, daemon=True).start()

    def action_open_example(self, rel):
        path = EXAMPLES / rel
        self.confirm_discard(lambda: self.load_file(path))

    def action_about(self):
        about = Adw.AboutDialog(application_name="backingtrack", version=__version__,
                                comments="Backing track con chitarra e batteria campionate, dai tuoi accordi.",
                                website="https://github.com/wdog/backingtrack", license_type=Gtk.License.MIT_X11,
                                developers=["backingtrack contributors"], application_icon=APP_ID)
        about.add_credit_section("Campioni", ["Black & Green Guitars — Karoryfer Samples (CC0)",
                                              "Salamander Drumkit — Alexander Holm (CC-BY-SA 3.0)",
                                              "IR casse — Jester Dyne Productions",
                                              "Contrabbasso — D. Smolken (CC0)"])
        about.present(self)

    # riproduzione ---------------------------------------------------------
    def _on_key(self, _ctrl, keyval, _code, state):
        """Spazio = play/pausa, B = da capo, S = stop. Non attive mentre si scrive in un campo."""
        if state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.ALT_MASK | Gdk.ModifierType.SUPER_MASK):
            return False
        focus = self.get_focus()
        if isinstance(focus, Gtk.Editable) or isinstance(focus, Gtk.TextView):
            return False
        action = {Gdk.KEY_space: self.play_toggle, Gdk.KEY_b: self.play_restart, Gdk.KEY_B: self.play_restart,
                  Gdk.KEY_s: self.play_stop, Gdk.KEY_S: self.play_stop}.get(keyval)
        if action:
            action()
            return True
        return False

    def _ready(self):
        if self.player.media is None:
            self.toast("Niente da suonare: premi Genera e ascolta (Ctrl+R)")
            return False
        return True

    def play_toggle(self):
        if self._ready():
            self.player.toggle()

    def play_restart(self):
        if self._ready():
            self.player.restart()

    def play_stop(self):
        if self._ready():
            self.player.stop()

    def open_output_dir(self):
        wav = getattr(self, "last_output", None)
        if wav:
            Gtk.FileLauncher.new(Gio.File.new_for_path(str(Path(wav).resolve()))).open_containing_folder(
                self, None, None)


EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
DRAFT = packs.data_dir() / "bozza.json"


def build_menu():
    """Barra menu classica: File, Brano, Aiuto."""
    menubar = Gio.Menu()
    file_menu = Gio.Menu()
    sec = Gio.Menu()
    sec.append("Nuovo", "app.new")
    sec.append("Apri…", "app.open")
    if EXAMPLES.is_dir():
        examples = Gio.Menu()
        for style in sorted(p for p in EXAMPLES.iterdir() if p.is_dir()):
            sub = Gio.Menu()
            for f in sorted(style.glob("*.yaml")):
                sub.append(f.stem.replace("_", " ").capitalize(),
                           "app.open-example(%s)" % GLib.Variant.new_string("%s/%s" % (style.name, f.name)).print_(False))
            examples.append_submenu(style.name.capitalize(), sub)
        sec.append_submenu("Apri esempio", examples)
    file_menu.append_section(None, sec)
    sec = Gio.Menu()
    sec.append("Salva", "app.save")
    sec.append("Salva con nome…", "app.save-as")
    file_menu.append_section(None, sec)
    sec = Gio.Menu()
    sec.append("Esci", "app.quit")
    file_menu.append_section(None, sec)
    menubar.append_submenu("_File", file_menu)

    sec_menu = Gio.Menu()
    part = Gio.Menu()
    part.append("Nuova sezione", "app.section-new")
    part.append("Duplica sezione", "app.section-dup")
    part.append("Elimina sezione", "app.section-del")
    sec_menu.append_section(None, part)
    part = Gio.Menu()
    part.append("Sposta su", "app.section-up")
    part.append("Sposta giù", "app.section-down")
    sec_menu.append_section(None, part)
    part = Gio.Menu()
    part.append("Nuova battuta", "app.bar-new")
    part.append("Duplica battuta", "app.bar-dup")
    sec_menu.append_section(None, part)
    menubar.append_submenu("_Sezione", sec_menu)

    play_menu = Gio.Menu()
    for label, action, accel in (("Play / pausa", "app.play-toggle", "space"), ("Da capo", "app.play-restart", "b"),
                                 ("Stop", "app.play-stop", "s")):
        item = Gio.MenuItem.new(label, action)
        item.set_attribute_value("accel", GLib.Variant.new_string(accel))  # solo indicazione: gestite dal tasto
        play_menu.append_item(item)

    song_menu = Gio.Menu()
    song_menu.append("Genera e ascolta", "app.render")
    song_menu.append("Apri cartella output", "app.open-output")
    song_menu.append("Installa campioni mancanti", "app.install")
    menubar.append_submenu("_Brano", song_menu)
    menubar.append_submenu("_Riproduzione", play_menu)

    help_menu = Gio.Menu()
    help_menu.append("Guida online", "app.help")
    help_menu.append("Informazioni", "app.about")
    menubar.append_submenu("_Aiuto", help_menu)
    return menubar


def make_waveform(wav):
    """PNG trasparente con la forma d'onda (ffmpeg), per la barra del player. None se non riesce."""
    import shutil
    import subprocess
    import tempfile
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    png = Path(tempfile.gettempdir()) / ("backingtrack-wave-%d.png" % abs(hash(str(wav))))
    p = subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(wav), "-filter_complex",
                        "aformat=channel_layouts=mono,showwavespic=s=1600x120:colors=#f5a623:scale=lin",
                        "-frames:v", "1", str(png)], stdin=subprocess.DEVNULL)
    return png if p.returncode == 0 else None


def slug(text):
    s = re.sub(r"[^\w]+", "_", (text or "brano").lower(), flags=re.UNICODE).strip("_")
    return s or "brano"


class App(Adw.Application):
    def __init__(self, path=None):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.path = path
        self.connect("activate", self._activate)

    def _activate(self, _app):
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        theme.add_search_path(str(Path(__file__).resolve().parent / "data"))
        Gtk.Window.set_default_icon_name(APP_ID)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        win = MainWindow(self, self.path)
        for name, accel, fn in (("new", "<Control>n", win.action_new), ("open", "<Control>o", win.action_open),
                                ("save", "<Control>s", win.action_save),
                                ("save-as", "<Control><Shift>s", win.action_save_as),
                                ("render", "<Control>r", win.action_render),
                                ("section-new", "<Control>t", win.add_section),
                                ("section-dup", "<Control>d", win.duplicate_section),
                                ("bar-new", "<Control>b", lambda: win.add_bar("")),
                                ("bar-dup", "<Control><Shift>d", win.duplicate_focused_bar),
                                ("quit", "<Control>q", win.close)):
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", lambda _a, _p, f=fn: f())
            self.add_action(act)
            self.set_accels_for_action("app." + name, [accel])
        for name, fn in (("open-output", win.open_output_dir), ("install", win.install_packs),
                         ("section-del", win.delete_section), ("play-toggle", win.play_toggle),
                         ("play-restart", win.play_restart), ("play-stop", win.play_stop), ("section-up", lambda: win.move_section(-1)),
                         ("section-down", lambda: win.move_section(1)),
                         ("about", win.action_about),
                         ("help", lambda: Gtk.UriLauncher.new("https://github.com/wdog/backingtrack#readme")
                          .launch(win, None, None))):
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", lambda _a, _p, f=fn: f())
            self.add_action(act)
        act = Gio.SimpleAction.new("open-example", GLib.VariantType.new("s"))
        act.connect("activate", lambda _a, p: win.action_open_example(p.get_string()))
        self.add_action(act)
        win.present()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if Gtk is None:
        sys.exit("serve PyGObject con GTK 4 e libadwaita: %s\n"
                 "Debian/Ubuntu: sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1\n"
                 "Fedora: sudo dnf install python3-gobject gtk4 libadwaita\n"
                 "Arch: sudo pacman -S python-gobject gtk4 libadwaita\n"
                 "macOS: brew install pygobject3 gtk4 libadwaita" % _GI_ERROR)
    path = argv[0] if argv and not argv[0].startswith("-") else None
    if "--version" in argv:
        print("backingtrack-gui", __version__)
        return 0
    return App(path).run([sys.argv[0]])


if __name__ == "__main__":
    sys.exit(main())
