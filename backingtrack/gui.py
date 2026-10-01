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
from . import theory
from .theory import Chord

APP_ID = "io.github.wdog.backingtrack"
GROOVE_NAMES = list(GROOVES)
SWING_HINT = "0 = ottavi dritti · 0.5 = swing leggero · 1 = shuffle terzinato"
TRI = ["dal groove", "sì", "no"]
TRI_VAL = [None, True, False]

SECTION_COLORS = ["#ffb86c", "#8be9fd", "#50fa7b", "#bd93f9", "#f1fa8c", "#ff79c6", "#ff5555", "#6272a4"]  # Dracula
STYLE_EMOJI = {"rock": "🤘", "blues": "🎷", "rockabilly": "🕺", "country": "🤠", "jazz": "🎺",
               "funk": "🪩", "reggae": "🌴", "soul": "🎤"}

# Guida (menu Aiuto › Guida, F1): pagine (titolo, icona, voci). Voce: ("p", testo) paragrafo, ("h", titolo)
# sottotitolo, ("code", [(esempio, significato)]) tabella di esempi, (termine, spiegazione) riga di una scheda.
# Il testo è Pango markup.
BAR_EXAMPLES = ("code", [("A", "A per tutti e 4 i tempi"), ("A D", "A 2 tempi, D 2"),
                         ("C G Am F", "un accordo per tempo"),
                         ("Em . D C", "«.» prolunga l'accordo prima: Em 2 tempi, D 1, C 1"),
                         ("%", "ripete la battuta precedente"), ("N.C.", "pausa: la chitarra tace")])
CHORD_EXAMPLES = ("code", [("C D E F G A B", "Do Re Mi Fa Sol La Si (il Si è B, non H)"),
                           ("F#  Bb", "diesis con #, bemolle con b"),
                           ("A  Am  A7", "maggiore, minore, settima"),
                           ("Amaj7  Am7  A5", "settima maggiore, minore settima, power chord"),
                           ("Asus4  Adim  A9", "anche 6, m6, add9, 13, 7#9, sus2, 7sus4, dim7, m7b5, aug"),
                           ("D/F#", "accordo slash: D con F# al basso")])
HELP = [
    ("Inizio", "🎸", [
        ("p", "Scrivi gli accordi di un brano, scegli uno stile e premi <b>Genera e ascolta</b>: il programma "
              "suona chitarra ritmica e batteria (e il basso, se lo attivi) sui tuoi accordi. "
              "Tu suoni sopra: assolo, melodia, canto."),
        ("Brano", "tempo, stile e scaletta: quali sezioni suonano e in che ordine"),
        ("Sezione", "un pezzo del brano (intro, strofa, ritornello…) che si può ripetere"),
        ("Battuta", "una casella con gli accordi di 4 tempi"),
        ("Groove", "lo stile di accompagnamento: ritmo di chitarra e batteria, ampli, swing"),
        ("h", "In tre passi"),
        ("1", "scheda <b>Sezioni</b>: scrivi gli accordi, oppure parti da un <b>modello di giro</b>"),
        ("2", "scheda <b>Brano</b>: tempo, groove e ordine delle sezioni"),
        ("3", "<b>Genera e ascolta</b> (Alt+G): il brano parte nel player in basso"),
    ]),
    ("Brano", "🎵", [
        ("Titolo", "nome del brano e del file generato"),
        ("Tempo (BPM)", "battiti al minuto: 60 lento, 120 medio, 180 veloce"),
        ("Groove", "stile di tutto il brano; ogni sezione può cambiarlo"),
        ("Basso", "contrabbasso o basso elettrico (campioni da Brano › Installa campioni mancanti)"),
        ("Ordine delle sezioni", "la scaletta, es. Intro, Strofa ×2, Ritornello. Vuota = ordine della scheda "
                                 "Sezioni, ognuna con le sue ripetizioni"),
        ("h", "Avanzate"),
        ("Suono", "chitarra, ampli (da pulito a distorto), chitarra doppiata L/R, slapback, voicing "
                  "(barré, aperti, jazz, triadi)"),
        ("Struttura", "conteggio iniziale, finale con accordo lungo, rullate a fine sezione, piatto sugli attacchi"),
        ("Trasposizione", "sposta tutto il brano di semitoni: −1 = mezzo tono sotto"),
        ("Swing", "0 = ottavi dritti, 0.5 = swing leggero, 1 = shuffle"),
        ("Umanizzazione", "0 = tempo perfetto, 2 = molto sciolto"),
        ("Velocità pennata", "millisecondi tra una corda e l'altra"),
        ("Variazione", "un altro numero = altre dinamiche e altri campioni"),
        ("Output", "cartella, MP3, tracce separate (stems) per un DAW"),
    ]),
    ("Sezioni", "🧩", [
        ("p", "A sinistra l'elenco delle sezioni, al centro gli accordi, a destra le impostazioni."),
        ("h", "Battute"),
        ("p", "Una casella = una battuta di 4 tempi. Più accordi si dividono i tempi in parti uguali."),
        BAR_EXAMPLES,
        ("p", "Invio = battuta successiva · trascina ⠿ per spostare · tasto destro = menu."),
        ("h", "Strumenti"),
        ("Tavolozza", "le 12 note (alterazione sotto la sua nota) e gli accordi già usati: clic = aggiungi alla "
                      "battuta selezionata (o nuova battuta se non ce n'è), trascina = mettilo su una battuta. "
                      "Una nota = accordo maggiore: m, 7… si scrivono nella battuta"),
        ("+ %  + N.C.", "aggiungono una battuta che ripete o una pausa"),
        ("h", "Impostazioni della sezione"),
        ("Ripetizioni", "quante volte suona di fila"),
        ("Groove", "vuoto = quello del brano"),
        ("Dinamica", "1 = normale, 0.8 = più piano (Avanzate)"),
        ("Chitarra, Batteria", "spegnile per un'intro di sola batteria o uno stop (Avanzate)"),
    ]),
    ("Accordi", "🎼", [
        ("p", "Notazione inglese, tonica maiuscola."),
        CHORD_EXAMPLES,
        ("p", "Una battuta sbagliata diventa rossa: il tooltip dice cosa correggere."),
    ]),
    ("Tonalità", "🔑", [
        ("p", "I <b>modelli di giro</b> (12-bar blues, I-V-vi-IV…) sono scritti <b>a gradi</b>: I, IV e V sono "
              "il primo, il quarto e il quinto accordo della scala. La <b>Tonalità</b> dice da che nota partire "
              "e trasforma i gradi in accordi veri."),
        ("code", [("in A", "A7  D7  E7"), ("in E", "E7  A7  B7"), ("in G", "G7  C7  D7")]),
        ("p", "Scegli la tonalità del brano che vuoi suonare, o quella comoda per voce e strumento. "
              "Il tooltip del modello mostra gli accordi che ottieni."),
        ("Sostituisci accordi", "cancella le battute della sezione e ci mette il giro"),
        ("Aggiungi in coda", "mette il giro dopo le battute che ci sono"),
        ("p", "Nessuno dei due traspone: per spostare un brano già scritto usa <b>Trasposizione</b> "
              "(Brano › Avanzate)."),
        ("h", "Tonica o tonalità?"),
        ("p", "Pensa a una città con le sue vie. La <b>tonalità</b> è la città: dice dove si gioca tutto il brano. "
              "La <b>tonica</b> è il numero civico di una casa: è la nota su cui è costruito <b>un singolo "
              "accordo</b>. Un brano ha una tonalità sola, ma tanti accordi, ognuno con la sua tonica."),
        ("h", "Esempio: blues in A"),
        ("p", "Il 12-bar blues usa tre accordi: I, IV e V grado. In <b>tonalità A</b> diventano:"),
        ("code", [("A7", "I grado · tonica A · è «casa», da qui si parte e qui si torna"),
                  ("D7", "IV grado · tonica D · ci si allontana un po'"),
                  ("E7", "V grado · tonica E · tensione, vuole tornare ad A7")]),
        ("p", "Le 12 battute (è il modello «12-bar blues» con tonalità A):"),
        ("code", [("battute 1–4", "A7  A7  A7  A7"), ("battute 5–8", "D7  D7  A7  A7"),
                  ("battute 9–12", "E7  D7  A7  E7")]),
        ("p", "Tre toniche diverse (A, D, E), <b>una sola tonalità: A</b>. Il brano «è in A» perché gira intorno "
              "ad A7 e finisce lì."),
        ("h", "Cosa cambia se tocchi l'una o l'altra"),
        ("Tonica", "cambi <b>un accordo</b>: scrivi G7 al posto di D7 nella battuta 5 e cambia solo "
                   "quella battuta"),
        ("Tonalità (modelli)", "cambi <b>tutto il giro</b>, sempre con la stessa forma: lo stesso blues "
                               "in E diventa E7 · A7 · B7, in G diventa G7 · C7 · D7"),
        ("p", "In pratica: tonalità A = blues comodo per la chitarra; tonalità E = più grave, classico del "
              "Chicago blues. Scegli la tonalità in cui canti o suoni meglio, il giro resta lo stesso."),
    ]),
    ("Scale", "🎸", [
        ("p", "Scheda <b>Sezioni › Scale</b>: la tastiera mostra dove stanno le note di una scala, per improvvisare "
              "sopra la base. Corda 1 (mi cantino) in alto, come nelle tablature."),
        ("Pentatoniche e blues", "pentatonica minore e maggiore (5 note), blues minore (+ b5) e maggiore (+ b3)"),
        ("Maggiore e minori", "maggiore, minore naturale, armonica (7 maggiore) e melodica (6 e 7 maggiori)"),
        ("Modi", "dorica (minore con la 6), misolidia (maggiore con la b7), lidia (#4), frigia (b2)"),
        ("code", [("● viola", "tonica: la nota «casa», dove le frasi si chiudono bene"),
                  ("● rosa", "blue note nei blues; nei modi la nota caratteristica, quella che dà il colore"),
                  ("● azzurro", "le altre note della scala")]),
        ("h", "Sistema CAGED"),
        ("p", "Gli accordi aperti C, A, G, E e D, spostati lungo il manico, dividono la tastiera in <b>5 box</b> "
              "che si incastrano: ogni box è una posizione in cui la mano suona la scala senza spostarsi. "
              "Nelle scale minori le forme sono minori (Em, Dm…)."),
        ("p", "Blues minore in A: il box <b>Em</b> sta ai tasti 5–8 (il «box 1» che si impara per primo), poi "
              "Dm 7–10, Cm 9–13, Am 12–15, Gm 2–5. Dopo il 12 tutto si ripete un'ottava sopra."),
        ("Box CAGED", "Tutti = il manico intero. Clic su un box per vederlo da solo, poi sui box accanto per "
                      "unirli (es. Em + Dm = tasti 5–10); clic su quello all'estremità per toglierlo. "
                      "Si possono cliccare anche le fasce colorate sulla tastiera"),
        ("Etichette", "Note (A, C, D…) o Gradi (1, b3, 4…): i gradi valgono in ogni tonalità"),
    ]),
    ("Player", "▶️", [
        ("Forma d'onda", "le sezioni a colori; clic = salta lì"),
        ("Striscia accordi", "ogni battuta: a sinistra il numero nel brano, a destra nella sezione (3/12)"),
        ("Posizione", "sotto il tempo: «Battuta 15 / 64 · Strofa 3 / 12»"),
        ("code", [("Spazio", "play / pausa"), ("B", "da capo"), ("S", "stop"), ("L", "loop acceso / spento")]),
        ("h", "Loop"),
        ("p", "Per studiare un passaggio: accendi il loop 🔁 e scegli da che battuta a che battuta suonare. "
              "Arrivato alla fine, il player torna all'inizio del tratto. Il tratto è segnato in rosa "
              "sulla forma d'onda e sotto le battute."),
        ("Shift+clic", "su una battuta della striscia: fine del loop (o nuovo inizio, se è prima)"),
    ]),
    ("Tasti", "⌨️", [
        ("code", [("Alt+G  Ctrl+R", "genera e ascolta"), ("Ctrl+N  Ctrl+O", "nuovo, apri"),
                  ("Ctrl+S", "salva"), ("Ctrl+Shift+S", "salva con nome"),
                  ("Ctrl+T  Ctrl+D", "nuova sezione, duplica sezione"),
                  ("Ctrl+B  Super+N", "nuova battuta"), ("Ctrl+Shift+D", "duplica battuta"),
                  ("Super+Canc", "elimina la battuta selezionata"), ("F9  Shift+F9", "mostra / nascondi elenco sezioni, impostazioni"),
                  ("Spazio  B  S  L", "play/pausa, da capo, stop, loop"), ("F1", "guida"), ("Ctrl+Q", "esci")]),
    ]),
]


def help_page(items):
    """Una pagina della guida: paragrafi, sottotitoli e schede (termine | spiegazione o esempio | significato)."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    card = None
    for kind, body in items:
        if kind == "p":
            box.append(Gtk.Label(label=body, use_markup=True, wrap=True, xalign=0))
            card = None
        elif kind == "h":
            h = Gtk.Label(label=body, xalign=0, margin_top=8)
            h.add_css_class("heading")
            box.append(h)
            card = None
        else:
            if card is None or kind == "code":
                card, row = Gtk.Grid(column_spacing=16, row_spacing=8), 0
                card.add_css_class("help-card")
                box.append(card)
            for left, right in (body if kind == "code" else [(kind, body)]):
                term = Gtk.Label(label=left, xalign=0, valign=Gtk.Align.START)
                term.add_css_class("help-code" if kind == "code" else "help-term")
                card.attach(term, 0, row, 1, 1)
                card.attach(Gtk.Label(label=right, use_markup=True, wrap=True, xalign=0, hexpand=True), 1, row, 1, 1)
                row += 1
            if kind == "code":
                card = None
    return box


CSS = ("""
/* tema Dracula (https://draculatheme.com): sfondi e testo, forzato scuro in App._activate */
@define-color window_bg_color #282a36;
@define-color window_fg_color #f8f8f2;
@define-color view_bg_color #282a36;
@define-color view_fg_color #f8f8f2;
@define-color headerbar_bg_color #21222c;
@define-color headerbar_fg_color #f8f8f2;
@define-color sidebar_bg_color #21222c;
@define-color sidebar_fg_color #f8f8f2;
@define-color card_bg_color #343746;
@define-color card_fg_color #f8f8f2;
@define-color popover_bg_color #343746;
@define-color popover_fg_color #f8f8f2;
@define-color dialog_bg_color #343746;
@define-color dialog_fg_color #f8f8f2;
@define-color success_color #50fa7b;
@define-color warning_color #ffb86c;
@define-color error_color #ff5555;
@define-color destructive_color #ff5555;
:root { --window-bg-color: #282a36; --window-fg-color: #f8f8f2; --view-bg-color: #282a36; --view-fg-color: #f8f8f2;
        --headerbar-bg-color: #21222c; --headerbar-fg-color: #f8f8f2; --sidebar-bg-color: #21222c;
        --sidebar-fg-color: #f8f8f2; --card-bg-color: #343746; --card-fg-color: #f8f8f2;
        --popover-bg-color: #343746; --popover-fg-color: #f8f8f2; --dialog-bg-color: #343746;
        --dialog-fg-color: #f8f8f2; --success-color: #50fa7b; --warning-color: #ffb86c;
        --error-color: #ff5555; --destructive-color: #ff5555; }
window, .background { background-color: #282a36; color: #f8f8f2; }
popover.background { background-color: transparent; }  /* .background colpisce anche i popup: solo contents è pieno */
menubar > item { border: none; border-radius: 6px; padding: 4px 10px; }
menubar > item:selected { background-color: alpha(#bd93f9, 0.28); color: #f8f8f2; box-shadow: none; border: none; }
headerbar, .navigation-sidebar, popover > contents { background-color: #21222c; color: #f8f8f2; }
selection { background-color: alpha(#bd93f9, 0.35); }
:root { --accent-bg-color: #bd93f9; --accent-fg-color: #282a36; --accent-color: #caa9fa; }
@define-color accent_bg_color #bd93f9;
@define-color accent_fg_color #282a36;
@define-color accent_color #caa9fa;
stackswitcher button:checked { color: #caa9fa; }
entry:focus-within { outline-color: alpha(#caa9fa, 0.7); }
.emoji { font-size: 1.25em; min-width: 1.6em; }
.dot { font-size: 1.4em; }
.status-ok { color: @success_color; }
.status-bad { color: @warning_color; }
.big-emoji { font-size: 3.5em; }
window button.render-btn { font-weight: 800; letter-spacing: 0.02em; color: #282a36; border: none; border-radius: 10px;
                    padding: 5px 8px 5px 16px; min-height: 30px;
                    background: linear-gradient(135deg, #caa9fa 0%, #bd93f9 55%, #ff79c6 100%);
                    box-shadow: 0 2px 10px alpha(#bd93f9, 0.45), inset 0 1px alpha(white, 0.35); }
window button.render-btn:hover { background: linear-gradient(135deg, #d6bcfb 0%, #caa9fa 55%, #ff92d0 100%);
                          box-shadow: 0 3px 14px alpha(#bd93f9, 0.65), inset 0 1px alpha(white, 0.45); }
window button.render-btn:active { background: linear-gradient(135deg, #bd93f9, #9a6fe0); box-shadow: inset 0 2px 4px alpha(black, 0.3); }
window button.render-btn:disabled { background: alpha(#bd93f9, 0.30); color: alpha(#282a36, 0.6); box-shadow: none; }
window button.render-btn image { -gtk-icon-size: 18px; }
.keycap { font-size: 0.72em; font-weight: 700; padding: 1px 7px; border-radius: 6px;
          background: alpha(black, 0.22); color: alpha(white, 0.9); }
.adv-toggle { font-size: 0.9em; }
togglebutton.adv-toggle:checked, button.adv-toggle:checked { background: alpha(#bd93f9, 0.25); color: #caa9fa; }
viewswitcher button:checked { color: #caa9fa; box-shadow: inset 0 -3px #bd93f9; }
.bar-num { font-size: 0.95em; font-weight: bold; color: #bd93f9; font-feature-settings: "tnum"; }
.bar-entry { font-weight: bold; font-size: 1.1em; }
.bar-reading { font-size: 0.8em; opacity: 0.75; }
.help-card { background: alpha(currentColor, 0.045); border-radius: 12px; padding: 12px 16px; }
.help-term { font-weight: 700; color: #bd93f9; }
.help-code { font-family: monospace; font-weight: 700; color: #50fa7b; background: alpha(black, 0.25);
             border-radius: 6px; padding: 1px 8px; }
.help-side { min-width: 170px; background: #21222c; }
.yaml-view { font-family: monospace; padding: 12px; }
.summary { padding: 4px 12px; }
.player { padding: 12px 16px 6px 16px; background: linear-gradient(to bottom, alpha(#bd93f9, 0.10), alpha(#bd93f9, 0.03));
          border-top: 1px solid alpha(#bd93f9, 0.35); }
.player button.play-btn { min-width: 48px; min-height: 48px; -gtk-icon-size: 22px; padding: 0;
                          background: #bd93f9; color: #282a36; border: none; outline: none;
                          box-shadow: 0 2px 6px alpha(black, 0.3); }
.player button.play-btn:hover { background: #caa9fa; }
.player .transport button.circular { min-width: 34px; min-height: 34px; }
.player-title { font-weight: bold; font-size: 1.05em; }
.player-time { font-feature-settings: "tnum"; font-size: 1.35em; font-weight: 300; }
.player-total { font-feature-settings: "tnum"; opacity: 0.55; font-size: 0.9em; }
.player .loop spinbutton { min-width: 0; min-height: 28px; }
.player .loop spinbutton > text { padding: 0 2px 0 8px; }
.player .loop spinbutton > button { min-width: 14px; min-height: 14px; padding: 0 3px; -gtk-icon-size: 10px; }
.player .loop button.circular:checked { background-color: #ff79c6; color: #282a36; }
.player-pos { font-feature-settings: "tnum"; font-size: 0.8em; opacity: 0.75; }
.player scale trough highlight { background: #bd93f9; }
.player scale slider { background: #caa9fa; }
.picker { font-weight: 600; }
.bar-grid { margin-top: 4px; }
.bar-cell { padding: 4px 6px 4px 4px; border-radius: 6px; background: alpha(currentColor, 0.06);
            border-left: 4px solid alpha(currentColor, 0.3); min-height: 34px; }
.bar-cell.bad { background: alpha(@error_color, 0.18); border-left-color: @error_color; }
.bar-cell.drop-hover, .bar-add.drop-hover { background: alpha(#bd93f9, 0.35); }
.bar-cell entry { background: transparent; box-shadow: none; min-height: 26px; padding: 0 2px; }
.bar-handle { opacity: 0.35; font-size: 1.1em; padding: 0 2px; }
.bar-handle:hover { opacity: 0.9; }
.bar-add { min-height: 34px; font-size: 1.2em; }
.chip { padding: 2px 10px; min-height: 26px; min-width: 22px; border-radius: 8px; font-weight: bold; }
toggle-group { background: alpha(currentColor, 0.08); border-radius: 10px; padding: 3px; }
toggle-group > toggle { padding: 4px 11px; margin: 0 1px; border-radius: 8px; font-weight: 600; min-height: 24px; }
toggle-group > toggle:hover { background: alpha(currentColor, 0.08); }
toggle-group > toggle:checked { background: #bd93f9; color: #282a36; }
toggle-group > separator { background: transparent; min-width: 0; }
.grid-choice { min-width: 44px; font-weight: 600; }
.wave { border-radius: 8px; background: alpha(currentColor, 0.06); }
.builder { padding: 12px; }

/* ---- controlli: stile proprio, indipendente dal tema di sistema (Arc & co. li fanno piatti e squadrati).
   Solo dentro .bt-main (il contenuto della finestra): i dialoghi (salva, conferme) restano quelli di sistema. */
.bt-main button, .bt-main menubutton > button, .bt-main spinbutton > button {
    border: none; border-radius: 8px; box-shadow: none; background-image: none; text-shadow: none;
    background-color: alpha(currentColor, 0.08); padding: 4px 12px; min-height: 26px;
    transition: background-color 120ms ease, box-shadow 120ms ease; }
.bt-main button:hover, .bt-main menubutton > button:hover { background-color: alpha(currentColor, 0.14); }
.bt-main button:active, .bt-main button:checked, .bt-main menubutton > button:checked {
    background-color: alpha(currentColor, 0.20); }
.bt-main button:disabled { opacity: 0.45; }
.bt-main button.flat, .bt-main menubutton.flat > button, .bt-main button.image-button.flat,
.bt-main headerbar button:not(.render-btn), .bt-main spinbutton > button {
    background-color: transparent; }
.bt-main button.flat:hover, .bt-main headerbar button:not(.render-btn):hover, .bt-main spinbutton > button:hover {
    background-color: alpha(currentColor, 0.10); }
.bt-main button.image-button { padding: 4px 7px; }
.bt-main button.circular { border-radius: 999px; padding: 4px; min-width: 30px; min-height: 30px; }
.bt-main button.suggested-action, .bt-main menubutton.suggested-action > button {
    color: #282a36; font-weight: 600;
    background-image: linear-gradient(to bottom, #caa9fa, #a67ef0);
    box-shadow: 0 1px 3px alpha(black, 0.25), inset 0 1px alpha(white, 0.25); }
.bt-main button.suggested-action:hover { background-image: linear-gradient(to bottom, #d6bcfb, #bd93f9); }
.bt-main button.suggested-action:active { background-image: linear-gradient(to bottom, #9a6fe0, #8a5fd8); }
.bt-main button.danger, .bt-main button.destructive-action {
    background-color: alpha(#ff5555, 0.14); color: #ff6e6e; background-image: none; }
.bt-main button.danger:hover, .bt-main button.destructive-action:hover { background-color: alpha(#ff5555, 0.30); color: white; }
.bt-main button.pill { border-radius: 10px; padding: 10px 26px; }

/* schede (Brano/Sezioni/YAML, Accordi/Scale): niente riquadro da pulsante, solo testo e sottolineatura.
   Il tema di sistema (Qogir & co.) le fa squadrate con padding proprio: qui si azzera e si ridefinisce tutto. */
.bt-main viewswitcher button.toggle { background: transparent; box-shadow: none; border: none; border-radius: 0;
    padding: 0; margin: 0 4px; min-height: 0; }
.bt-main viewswitcher button.toggle > stack > box.wide { padding: 8px 14px; border-spacing: 8px; }
.bt-main viewswitcher button.toggle > stack > box.narrow { padding: 4px 10px; }
.bt-main viewswitcher button.toggle:hover { background: transparent; color: #f8f8f2;
    box-shadow: inset 0 -2px alpha(currentColor, 0.25); }
.bt-main viewswitcher button.toggle:checked, .bt-main viewswitcher button.toggle:checked:hover {
    background: transparent; color: #caa9fa; box-shadow: inset 0 -3px #bd93f9; }

/* voci dei menu a comparsa: evidenziazione viola invece del blu del tema di sistema */
popover.menu > contents { padding: 6px; border-radius: 12px; }
popover.menu modelbutton { padding: 0 12px; border-radius: 6px; min-height: 30px; }
popover.menu modelbutton > accelerator { margin-left: 28px; opacity: 0.55; }
popover.menu separator { margin: 4px 6px; }
popover.menu modelbutton:hover, popover.menu modelbutton:selected {
    background-color: alpha(#bd93f9, 0.28); color: #f8f8f2; }

/* menu a scelta (groove, ampli, note…) */
.bt-main menubutton.picker > button, .bt-main button.picker {
    background-color: alpha(currentColor, 0.07); border-radius: 8px; padding: 4px 10px;
    box-shadow: inset 0 0 0 1px alpha(currentColor, 0.08); }
.bt-main menubutton.picker > button:hover { background-color: alpha(currentColor, 0.13); }
.bt-main menubutton.picker > button:checked { background-color: alpha(#bd93f9, 0.25);
                                            box-shadow: inset 0 0 0 1px alpha(#bd93f9, 0.6); }

/* campi di testo e numeri */
.bt-main spinbutton, .bt-main entry {
    border: none; border-radius: 8px; box-shadow: inset 0 0 0 1px alpha(currentColor, 0.10);
    background-color: alpha(currentColor, 0.05); background-image: none; min-height: 30px; }
.bt-main spinbutton:focus-within, .bt-main entry:focus-within {
    box-shadow: inset 0 0 0 2px alpha(#caa9fa, 0.75); outline: none; }
.bt-main spinbutton > text { padding: 0 8px; background: transparent; box-shadow: none; }
.bt-main row spinbutton { background-color: transparent; }
.bt-main entry > text { background: transparent; }

/* liste di impostazioni a schede arrotondate */
.bt-main list.boxed-list, .bt-main .boxed-list {
    border: none; border-radius: 12px; background-color: alpha(currentColor, 0.035);
    box-shadow: 0 0 0 1px alpha(currentColor, 0.07), 0 2px 6px alpha(black, 0.12); }
.bt-main list.boxed-list > row { border-color: alpha(currentColor, 0.06); background-color: transparent; }
.bt-main list.boxed-list > row:first-child { border-top-left-radius: 12px; border-top-right-radius: 12px; }
.bt-main list.boxed-list > row:last-child { border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }
.bt-main list.boxed-list > row.activatable:hover { background-color: alpha(currentColor, 0.04); }
.bt-main switch { border: none; border-radius: 999px; background-color: alpha(currentColor, 0.18); }
.bt-main switch > slider { border: none; border-radius: 999px; background: white; box-shadow: 0 1px 2px alpha(black, 0.3); }
.bt-main switch:checked { background-color: #bd93f9; }

/* barra laterale delle sezioni */
.navigation-sidebar > row { border-radius: 10px; margin: 2px 6px; }
.navigation-sidebar > row:hover { background-color: alpha(currentColor, 0.05); }
/* sezione selezionata: stesso gradiente di «Genera e ascolta», testo scuro */
.navigation-sidebar > row:selected, .navigation-sidebar > row:selected:hover {
    background-color: transparent; color: #282a36;
    background-image: linear-gradient(135deg, #caa9fa 0%, #bd93f9 55%, #ff79c6 100%);
    box-shadow: 0 2px 10px alpha(#bd93f9, 0.40), inset 0 1px alpha(white, 0.30); }
.navigation-sidebar > row:selected label:not(.dot) { color: #282a36; }
.navigation-sidebar > row:selected .dim-label { opacity: 0.7; }
.side-tools { padding-top: 6px; border-top: 1px solid alpha(currentColor, 0.08); }
.card.builder { border: none; border-radius: 12px; background-color: alpha(currentColor, 0.035);
                box-shadow: 0 0 0 1px alpha(currentColor, 0.07), 0 2px 6px alpha(black, 0.12); }
paned > separator { background: alpha(currentColor, 0.06); min-width: 1px; }

/* dialoghi (conferme, errori): il tema di sistema non ha gli stili libadwaita, qui padding e pulsanti */
dialog.alert sheet { border-radius: 16px; border: none; box-shadow: 0 8px 32px alpha(black, 0.45), 0 0 0 1px alpha(currentColor, 0.08); }
dialog.alert .message-area { padding: 28px 30px 22px 30px; border-spacing: 10px; }
dialog.alert .message-area label.heading { font-size: 1.25em; font-weight: 800; }
dialog.alert .message-area label.body { opacity: 0.85; }
dialog.alert .response-area { padding: 4px 18px 18px 18px; border-spacing: 10px; border: none; }
dialog.alert .response-area > button { border: none; border-radius: 10px; min-height: 36px; padding: 6px 18px;
    background-image: none; box-shadow: none; background-color: alpha(currentColor, 0.09); font-weight: 600; margin: 0; }
dialog.alert .response-area > button:hover { background-color: alpha(currentColor, 0.15); }
dialog.alert .response-area > button.suggested-action { background-color: #bd93f9; color: #282a36; }
dialog.alert .response-area > button.suggested-action:hover { background-color: #caa9fa; }
dialog.alert .response-area > button.destructive-action { background-color: alpha(#ff5555, 0.16); color: #ff6e6e; }
dialog.alert .response-area > button.destructive-action:hover { background-color: alpha(#ff5555, 0.32); color: white; }
dialog.alert separator { background: transparent; min-width: 0; min-height: 0; }
""" + "".join(
    ".sec-%d.bar-cell { border-left-color: %s; background: alpha(%s, 0.10); } .sec-%d.dot { color: %s; }\n"
    % (i, c, c, i, c) for i, c in enumerate(SECTION_COLORS))).encode()

# --------------------------------------------------------------------------- widget di supporto

def spin_row(title, lo, hi, step, digits=0, tip=None):
    """Riga numerica; la spiegazione va nel tooltip, così la pagina resta compatta."""
    row = Adw.SpinRow.new_with_range(lo, hi, step)
    row.set_title(title)
    row.set_digits(digits)
    if tip:
        row.set_tooltip_text(tip)
    return row


def tip(row, text):
    row.set_tooltip_text(text)
    return row


def group(title, rows, description=None):
    """PreferencesGroup con le righe (widget, emoji)."""
    g = Adw.PreferencesGroup(title=title, description=description)
    for w, e in rows:
        g.add(deco(w, e))
    return g


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


STYLE_NAMES = {"rock": "Rock", "blues": "Blues", "rockabilly": "Rockabilly", "country": "Country", "jazz": "Jazz",
               "funk": "Funk", "reggae": "Reggae", "soul": "Soul"}


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
        self.button = Gtk.MenuButton(valign=Gtk.Align.CENTER, always_show_arrow=True)
        # NESTED: ogni sottomenu è un popover a sé, largo quanto le sue voci (non quanto la più lunga di tutti)
        self.button.set_popover(Gtk.PopoverMenu.new_from_model_full(menu, Gtk.PopoverMenuFlags.NESTED))
        self.button.add_css_class("picker")
        self.button.insert_action_group("row", group)  # il pulsante funziona anche staccato dalla riga
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
    short = lambda t: t if len(t) <= 48 else t[:46].rstrip(" ,(") + "…"  # nel menu; intera nel sottotitolo

    def subtitle(n):
        if n:
            return desc(n)
        g = song_groove() if song_groove else None
        return "dal brano: %s — %s" % (g, desc(g)) if g in GROOVES else ""

    return MenuRow(title, ([""] if inherit else []) + GROOVE_NAMES, groups,
                   top=[""] if inherit else (),
                   item_label=lambda n: "🎵 come il brano" if not n else "%s — %s" % (n, short(desc(n))),
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


def note_rows(names):
    """Griglia di note: sopra le naturali, sotto ognuna la sua alterazione (C# o Db sotto C), come sul piano.

    None = casella vuota (sotto E e B), così le colonne restano allineate.
    """
    idx = {n: i for i, n in enumerate(names)}
    nat = "C D E F G A B".split()
    acc = [idx.get(n + "#", idx.get(up + "b")) for n, up in zip(nat, nat[1:] + nat[:1])]
    return [[idx.get(n) for n in nat], acc]


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

    def __init__(self, editor, index, text, color, digits=1):
        super().__init__(spacing=4)
        self.editor, self.index = editor, index
        self.add_css_class("bar-cell")
        self.add_css_class("sec-%d" % color)
        handle = Gtk.Label(label="⠿", tooltip_text="Trascina per spostare la battuta")
        handle.add_css_class("bar-handle")
        handle.set_cursor(Gdk.Cursor.new_from_name("grab"))
        drag_source(handle, lambda: "bar:%d" % index, self)
        self.append(handle)
        # allineato alla larghezza del numero più grande (99 battute -> " 1"), con spazi larghi quanto una cifra
        num = Gtk.Label(label=str(index + 1).rjust(digits, "\u2007"), valign=Gtk.Align.START)
        num.add_css_class("bar-num")
        self.append(num)
        self.entry = Gtk.Entry(text=text, width_chars=3, max_width_chars=14, hexpand=True, has_frame=False,
                               placeholder_text="es. A7")
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
        tip = ("⚠ " + err) if err else ("Battuta %d: %s\n\nA D = 2 tempi a testa · '.' prolunga · '%%' ripete · "
                                          "N.C. = pausa · pulsante ? per gli accordi" % (self.index + 1, reading))
        self.set_tooltip_text(tip)


def fmt_time(us):
    sec = max(0, int(us // 1_000_000))
    return "%d:%02d" % (sec // 60, sec % 60)


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def song_bars(song, sections):
    """Battute nel tempo, per la striscia accordi del player: [{start, dur, segs, section, color, first, num, local, size}].

    `num` è il numero della battuta nel brano (1…), None per conteggio e finale;
    `local` il numero nella sezione (1…`size`, come nell'editor), ricomincia a ogni ripetizione.
    """
    order, timeline = build_timeline(song)
    bar = 240 / float(song.get("tempo", 120))
    names = [s["name"] for s in sections]
    bars, t = [], 0.0
    if song.get("count_in", True):
        bars.append(dict(start=0.0, dur=bar, segs=[(0, 4, "1 · 2 · 3 · 4")], section="conteggio", color=None, first=True,
                         num=None))
        t = bar
    first_chord = None
    local = 0
    for n, b in enumerate(timeline, 1):
        local = 1 if b["first"] else local + 1
        segs = [(s0, d, c.name if c else "N.C.") for s0, d, c in b["segs"]]
        first_chord = first_chord or next((c.name for _, _, c in b["segs"] if c), None)
        name = b["sec"]["name"]
        bars.append(dict(start=t, dur=bar, segs=segs, section=name, first=b["first"], num=n,
                         local=local, size=len(b["sec"]["bars"]),
                         color=names.index(name) % len(SECTION_COLORS) if name in names else None))
        t += bar
    if song.get("ending", True) and first_chord:
        end = song.get("ending_chord")
        end = Chord(str(end), int(song.get("transpose", 0))).name if end else first_chord
        bars.append(dict(start=t, dur=bar * 2, segs=[(0, 4, end)], section="finale", color=None, first=True,
                         num=None))
    return bars


class ChordStrip(Gtk.ScrolledWindow):
    """Tutte le battute del brano in fila, ognuna larga quanto serve per leggere i suoi accordi.

    Scorre da sola seguendo la battuta in riproduzione (evidenziata); si può scorrere a mano.
    Clic su una battuta = salta lì.
    """
    BAR_MIN = 96      # larghezza minima di una battuta
    FONT = "Sans Bold 13"
    FONT_CUR = "Sans Bold 14"
    FONT_NUM = "Sans Bold 9"
    FONT_SEC = "Sans Bold 8"
    TOP = 16          # spazio sopra per il nome della sezione
    BOTTOM = 10       # spazio sotto per la barra di scorrimento (sovrapposta)

    def __init__(self, player):
        super().__init__(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC, vscrollbar_policy=Gtk.PolicyType.NEVER,
                         hexpand=True)
        self.player = player
        self.bars, self.xs, self.ws = [], [], []
        self.cur = -1
        self._manual_until = 0
        self.area = Gtk.DrawingArea()
        self.area.set_content_height(80)
        self.area.set_draw_func(self._draw)
        self.set_child(self.area)
        self.set_min_content_height(80)
        click = Gtk.GestureClick()
        click.connect("pressed", self._click)
        self.area.add_controller(click)
        self.area.set_tooltip_text("Clicca una battuta per saltare lì · scorri per vedere tutto il brano")
        # se l'utente scorre a mano, per qualche secondo non riprendo il controllo
        scroll = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll.connect("scroll", self._user_scroll)
        self.add_controller(scroll)

    def _user_scroll(self, *_a):
        self._manual_until = GLib.get_monotonic_time() + 4_000_000
        return False

    def _text_width(self, text, font):
        layout = self.area.create_pango_layout(text)
        layout.set_font_description(Pango.FontDescription.from_string(font))
        return layout.get_pixel_extents()[1].width

    def set_bars(self, bars):
        """Calcola larghezze e posizioni: ogni segmento (accordo) deve contenere il suo nome."""
        self.bars, self.xs, self.ws = bars or [], [], []
        x = 4
        for b in self.bars:
            need = self.BAR_MIN
            for _s0, d, name in b["segs"]:
                need = max(need, (self._text_width(name, self.FONT_CUR) + 18) * 4 / max(d, 0.25))
            need = max(need, self._text_width(b["section"], self.FONT_SEC) + 16 if b["first"] else 0)
            self.xs.append(x)
            self.ws.append(need)
            x += need + 6
        self.area.set_content_width(int(x + 4))
        self.cur = -1
        self.get_hadjustment().set_value(0)
        self.area.queue_draw()

    def current(self, t):
        for i, b in enumerate(self.bars):
            if b["start"] <= t < b["start"] + b["dur"]:
                return i
        return len(self.bars) - 1 if self.bars and t >= self.bars[-1]["start"] else 0

    def update(self):
        m = self.player.media
        if not self.bars or not m:
            return
        cur = self.current(m.get_timestamp() / 1e6)
        if cur != self.cur:
            self.cur = cur
            if GLib.get_monotonic_time() > self._manual_until:
                adj = self.get_hadjustment()
                # battuta corrente a circa un quarto da sinistra: si vede cosa arriva
                target = self.xs[cur] - adj.get_page_size() * 0.25
                adj.set_value(max(0, min(target, adj.get_upper() - adj.get_page_size())))
        self.area.queue_draw()

    @staticmethod
    def _layout(cr, text, font):
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(Pango.FontDescription.from_string(font))
        layout.set_text(text, -1)
        return layout, layout.get_pixel_extents()[1]

    def _text(self, cr, text, font, x, y, w, rgba):
        """Testo centrato orizzontalmente in [x, x+w] e verticalmente attorno a y."""
        layout, logical = self._layout(cr, text, font)
        cr.set_source_rgba(*rgba)
        cr.move_to(x + max(0, (w - logical.width) / 2), y - logical.height / 2)
        PangoCairo.show_layout(cr, layout)

    def _draw(self, _area, cr, _w, h):
        if not self.bars:
            return
        fg = self.get_color()
        ink = (fg.red, fg.green, fg.blue)
        m = self.player.media
        t = m.get_timestamp() / 1e6 if m else 0
        cur = self.current(t)
        top, bh = self.TOP, h - self.TOP - self.BOTTOM
        p = self.player
        loop = ((p.loop_from.get_value_as_int(), p.loop_to.get_value_as_int())
                if p.loop_btn.get_active() else None)
        for i, b in enumerate(self.bars):
            x, bwi = self.xs[i], self.ws[i]
            col = hex_rgb(SECTION_COLORS[b["color"]]) if b["color"] is not None else ink
            # riquadro
            if i == cur:
                cr.set_source_rgba(0.74, 0.58, 0.98, 0.35)
            else:
                cr.set_source_rgba(*ink, 0.04 if i < cur else 0.09)
            self._round(cr, x, top, bwi, bh, 7)
            cr.fill()
            if i == cur:
                cr.set_source_rgba(1.0, 0.47, 0.78, 0.9)
                cr.set_line_width(1.5)
                self._round(cr, x + 0.75, top + 0.75, bwi - 1.5, bh - 1.5, 6.5)
                cr.stroke()
            if b["color"] is not None:
                cr.set_source_rgba(*col, 0.95 if i >= cur else 0.5)
                cr.rectangle(x + 6, top, bwi - 12, 3)
                cr.fill()
            # nome sezione sopra la prima battuta
            if b["first"]:
                layout, _lg = self._layout(cr, b["section"], self.FONT_SEC)
                cr.set_source_rgba(*col, 0.95)
                cr.move_to(x + 4, 0)
                PangoCairo.show_layout(cr, layout)
            # numero di battuta in piccolo: nel brano a sinistra, nella sezione a destra
            if b["num"] is not None:
                cr.set_source_rgba(*ink, 1.0 if i == cur else 0.75)
                layout, _lg = self._layout(cr, str(b["num"]), self.FONT_NUM)
                cr.move_to(x + 6, top + 5)
                PangoCairo.show_layout(cr, layout)
                cr.set_source_rgba(*col, 1.0 if i == cur else 0.8)  # colore della sezione
                layout, lg = self._layout(cr, "%d/%d" % (b["local"], b["size"]), self.FONT_NUM)
                cr.move_to(x + bwi - 6 - lg.width, top + 5)
                PangoCairo.show_layout(cr, layout)
            # accordi
            mid = top + bh / 2 + 3
            for s0, d, name in b["segs"]:
                sx = x + s0 / 4 * bwi
                sw = d / 4 * bwi
                if s0 > 0:
                    cr.set_source_rgba(*ink, 0.22)
                    cr.rectangle(sx, top + 12, 1, bh - 22)
                    cr.fill()
                font = self.FONT_CUR if i == cur else self.FONT
                self._text(cr, name, font, sx, mid, sw, (*ink, 1.0 if i >= cur else 0.4))
            # battute nel loop: fascia rosa sotto
            if b["num"] and loop and loop[0] <= b["num"] <= loop[1]:
                cr.set_source_rgba(1.0, 0.47, 0.78, 0.9)
                left = 3 if b["num"] > loop[0] else 0     # unisce le fasce nello spazio tra le battute
                right = 3 if b["num"] < loop[1] else 0
                cr.rectangle(x - left, top + bh + 3, bwi + left + right, 3)
                cr.fill()
            # avanzamento nella battuta corrente
            if i == cur and b["dur"]:
                frac = max(0, min(1, (t - b["start"]) / b["dur"]))
                cr.set_source_rgba(1.0, 0.47, 0.78, 1)
                self._round(cr, x + 6, top + bh - 6, max(3, (bwi - 12) * frac), 3, 1.5)
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

    def _click(self, gesture, _n, x, _y):
        m = self.player.media
        shift = gesture.get_current_event_state() & Gdk.ModifierType.SHIFT_MASK
        for i, (bx, bw) in enumerate(zip(self.xs, self.ws)):
            if shift and bx <= x <= bx + bw and self.bars[i]["num"]:
                # Shift+clic: allarga il loop fino a questa battuta (o lo accorcia dall'inizio)
                p, n = self.player, self.bars[i]["num"]
                lo, hi = p.loop_from.get_value_as_int(), p.loop_to.get_value_as_int()
                if not p.loop_btn.get_active():
                    lo = hi = n
                p.set_loop(min(lo, n), n if n >= lo else hi)
                return
            if bx <= x <= bx + bw and m:
                m.seek(int(self.bars[i]["start"] * 1e6))
                self._manual_until = 0
                self.area.queue_draw()
                return


SCALE_DESC = {
    "Pentatonica minore": "5 note, la base di rock e blues: la prima da imparare",
    "Pentatonica maggiore": "5 note, solare: country, southern rock, pop",
    "Blues minore": "pentatonica minore + b5: il suono classico del blues",
    "Blues maggiore": "pentatonica maggiore + b3: più dolce, country e rock'n'roll",
    "Maggiore (ionica)": "la scala do-re-mi: melodie, pop, canzoni",
    "Minore naturale (eolia)": "la scala minore: ballate, rock malinconico",
    "Dorica": "minore con la 6 maggiore: funk, jazz, Santana, «Oye como va»",
    "Misolidia": "maggiore con la b7: rock, blues-rock, sopra gli accordi di settima",
    "Lidia": "maggiore con la #4: sognante, colonne sonore",
    "Frigia": "minore con la b2: spagnolo, flamenco, metal",
    "Minore armonica": "minore con la 7 maggiore: neoclassico, gipsy, sopra il V7 in minore",
    "Minore melodica": "minore con 6 e 7 maggiori: jazz",
}
CAGED_COLORS = {"C": "#ffb86c", "A": "#50fa7b", "G": "#f1fa8c", "E": "#8be9fd", "D": "#ff5555"}


def draw_text(cr, text, font, cx, cy, rgba):
    """Testo centrato in (cx, cy)."""
    layout = PangoCairo.create_layout(cr)
    layout.set_font_description(Pango.FontDescription.from_string(font))
    layout.set_text(text, -1)
    ext = layout.get_pixel_extents()[1]
    cr.set_source_rgba(*rgba)
    cr.move_to(cx - ext.width / 2 - ext.x, cy - ext.height / 2 - ext.y)
    PangoCairo.show_layout(cr, layout)


class Fretboard(Gtk.DrawingArea):
    """Manico (corda 1 in alto, tasti 0-15) con le note di una scala e i box CAGED colorati."""
    FRETS = 15

    def __init__(self, on_box_click=None):
        super().__init__(hexpand=True, content_height=265)
        self.set_size_request(520, -1)
        self.root, self.scale, self.shapes, self.degrees = 9, "Blues minore", "", False
        self.boxes_x = []  # (forma, x da, x a) dell'ultimo disegno, per il clic
        self.set_draw_func(self._draw)
        if on_box_click:  # clic su una fascia = seleziona/deseleziona quel box
            click = Gtk.GestureClick()
            click.connect("released", lambda _g, _n, x, _y: self._click(x, on_box_click))
            self.add_controller(click)

    def _click(self, x, callback):
        hits = [(abs((a + b) / 2 - x), shape) for shape, a, b in self.boxes_x if a <= x <= b]
        if hits:
            callback(min(hits)[1])

    def update(self, root, scale, shapes, degrees):
        """shapes: box selezionati in ordine CAGED ("" = tutti)."""
        self.root, self.scale, self.shapes, self.degrees = root, scale, shapes, degrees
        self.queue_draw()

    def _draw(self, _area, cr, w, h):
        left, right, top, bottom, open_w = 30, 12, 34, 36, 34
        fw = (w - left - right - open_w) / self.FRETS
        sh = (h - top - bottom) / 5

        def x0(f):  # bordo sinistro della casella del tasto f (0 = corde a vuoto)
            return left if f == 0 else left + open_w + (f - 1) * fw

        def xc(f):
            return left + open_w / 2 if f == 0 else x0(f) + fw / 2

        def y(string):  # corda 1 (mi cantino) in alto
            return top + (string - 1) * sh

        minor = theory.SCALES[self.scale]["minor"]
        boxes = theory.caged_boxes(self.root, self.scale, self.FRETS)
        self.boxes_x = [(shape, x0(a), x0(b) + (open_w if b == 0 else fw)) for shape, a, b in boxes]
        shown = [b for b in boxes if not self.shapes or b[0] in self.shapes]
        for i, (shape, a, b) in enumerate(shown):  # box CAGED: fasce colorate con la lettera sopra
            r, g, bl = hex_rgb(CAGED_COLORS[shape])
            xa, xb = x0(a), x0(b) + (open_w if b == 0 else fw)
            lane = i % 2  # box vicini si sovrappongono: lettere su due righe
            cr.set_source_rgba(r, g, bl, 0.16 if self.shapes else 0.10)
            cr.rectangle(xa + 1, top - 10, xb - xa - 2, h - top - bottom + 20)
            cr.fill()
            cr.set_source_rgba(r, g, bl, 0.8)
            cr.rectangle(xa + 1, 4 + lane * 13, xb - xa - 2, 2)
            cr.fill()
            draw_text(cr, shape + ("m" if minor else ""), "Sans Bold 9", (xa + xb) / 2, 12 + lane * 13,
                      (r, g, bl, 1))

        fg = (0.97, 0.97, 0.95)
        cr.set_source_rgba(0.38, 0.45, 0.64, 0.9)  # tasti
        for f in range(1, self.FRETS + 1):
            cr.rectangle(x0(f) + fw - 1, y(1), 2, y(6) - y(1))
            cr.fill()
        cr.set_source_rgba(*fg, 0.9)  # capotasto
        cr.rectangle(x0(1) - 3, y(1) - 1, 5, y(6) - y(1) + 2)
        cr.fill()
        for f in (3, 5, 7, 9, 15):  # segni sulla tastiera
            cr.set_source_rgba(0.38, 0.45, 0.64, 0.6)
            cr.new_sub_path()
            cr.arc(xc(f), (y(3) + y(4)) / 2, 4, 0, 6.3)
            cr.fill()
        for yy in ((y(2) + y(3)) / 2, (y(4) + y(5)) / 2):
            cr.new_sub_path()
            cr.arc(xc(12), yy, 4, 0, 6.3)
            cr.fill()
        for f in range(self.FRETS + 1):
            draw_text(cr, str(f), "Sans 8", xc(f), h - bottom / 2, (*fg, 0.5))
        names = "e B G D A E".split()
        for string in range(1, 7):
            cr.set_source_rgba(*fg, 0.55)
            cr.set_line_width(0.8 + (string - 1) * 0.3)
            cr.move_to(x0(1) - 2, y(string))
            cr.line_to(w - right, y(string))
            cr.stroke()
            draw_text(cr, names[string - 1], "Sans 9", left / 2, y(string), (*fg, 0.6))

        info = theory.SCALES[self.scale]
        note_names = theory.scale_names(self.root, self.scale)
        rad = min(fw, sh) * 0.4
        for string, f, iv in theory.fretboard_notes(self.root, self.scale, self.FRETS):
            inside = any(a <= f <= b for _s, a, b in shown)
            alpha = 1 if not self.shapes or inside else 0.25
            color = "#bd93f9" if iv == 0 else "#ff79c6" if iv == info["blue"] else "#8be9fd"
            cr.set_source_rgba(*hex_rgb(color), alpha)
            cr.new_sub_path()
            cr.arc(xc(f), y(string), rad, 0, 6.3)
            cr.fill()
            label = theory.degree(self.scale, iv) if self.degrees else note_names[(self.root + iv) % 12]
            draw_text(cr, label, "Sans Bold %d" % (8 if len(label) > 1 else 9), xc(f), y(string),
                      (0.16, 0.16, 0.21, alpha))


class Player(Gtk.Revealer):
    """Barra di riproduzione: pulsanti grandi, forma d'onda cliccabile, tempo, volume."""

    def __init__(self, win):
        # slide con durata 0: niente animazione (senza frame resterebbe a metà) e, da nascosto, altezza 0.
        # Con NONE o CROSSFADE il Revealer nascosto occupa comunque tutta l'altezza del player.
        super().__init__(transition_type=Gtk.RevealerTransitionType.SLIDE_UP, transition_duration=0,
                         reveal_child=False)
        self.set_visible(False)  # anche nascosto il Revealer chiede la larghezza minima del player: via del tutto
        self.win = win
        self.media = None
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.add_css_class("player")
        box = Gtk.Box(spacing=16)
        transport = Gtk.Box(spacing=6, valign=Gtk.Align.CENTER)
        transport.add_css_class("transport")

        self.btn_restart = self._button("media-skip-backward-symbolic", "Da capo (B)", self.restart)
        self.btn_play = self._button("media-playback-start-symbolic", "Play / pausa (Spazio)", self.toggle)
        self.btn_play.add_css_class("play-btn")
        self.btn_play.add_css_class("suggested-action")
        self.btn_stop = self._button("media-playback-stop-symbolic", "Stop (S)", self.stop)
        for b in (self.btn_restart, self.btn_play, self.btn_stop):
            transport.append(b)
        box.append(transport)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=1)
        self.title = Gtk.Label(xalign=0, ellipsize=3, max_width_chars=26, width_chars=14)
        self.title.add_css_class("player-title")
        times = Gtk.Box(spacing=6)
        self.time = Gtk.Label(xalign=0, label="0:00")
        self.time.add_css_class("player-time")
        self.total = Gtk.Label(xalign=0, valign=Gtk.Align.BASELINE, label="/ 0:00")
        self.total.add_css_class("player-total")
        self.time.set_valign(Gtk.Align.BASELINE)
        times.append(self.time)
        times.append(self.total)
        self.pos = Gtk.Label(xalign=0, ellipsize=3, max_width_chars=26)
        self.pos.add_css_class("player-pos")
        info.append(self.title)
        info.append(times)
        info.append(self.pos)
        box.append(info)

        # loop su un tratto: da battuta X a Y (numeri come nella striscia accordi)
        loop = Gtk.Box(spacing=4, valign=Gtk.Align.CENTER)
        loop.add_css_class("loop")
        self.loop_btn = Gtk.ToggleButton(icon_name="media-playlist-repeat-symbolic",
                                         tooltip_text="Loop da battuta a battuta (L) · Shift+clic su una battuta "
                                                      "della striscia per scegliere il tratto")
        self.loop_btn.add_css_class("circular")
        self.loop_btn.connect("toggled", lambda _b: self._loop_changed(jump=True))
        self.loop_from = Gtk.SpinButton.new_with_range(1, 1, 1)
        self.loop_to = Gtk.SpinButton.new_with_range(1, 1, 1)
        for sb in (self.loop_from, self.loop_to):
            sb.set_width_chars(2)
        for sb, other, sign in ((self.loop_from, self.loop_to, 1), (self.loop_to, self.loop_from, -1)):
            sb.set_tooltip_text("Prima battuta del loop" if sign > 0 else "Ultima battuta del loop")
            sb.set_valign(Gtk.Align.CENTER)
            # da ≤ a: spostarne uno trascina l'altro
            sb.connect("value-changed", lambda b, o=other, sg=sign: (
                o.set_value(b.get_value()) if (b.get_value() - o.get_value()) * sg > 0 else None,
                self._loop_changed()))
        loop.append(self.loop_btn)
        loop.append(self.loop_from)
        loop.append(Gtk.Label(label="–"))
        loop.append(self.loop_to)
        box.append(loop)
        self.loop_box = loop

        # forma d'onda + avanzamento disegnato sopra
        self.wave = Gtk.Picture(content_fit=Gtk.ContentFit.FILL, can_shrink=True, hexpand=True)
        self.progress = Gtk.DrawingArea(hexpand=True)
        self.progress.set_draw_func(self._draw)
        overlay = Gtk.Overlay(hexpand=True)
        overlay.set_size_request(80, 64)
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
        self.volume.set_size_request(60, -1)
        self.volume.connect("value-changed", lambda sc: self.media and self.media.set_volume(sc.get_value()))
        vol.append(self.volume)
        box.append(vol)
        self.vol_box = vol
        self.folder_btn = self._button("folder-open-symbolic", "Apri la cartella dei file generati", win.open_output_dir)
        box.append(self.folder_btn)
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
        self.strip.set_bars(bars or [])
        total = max([b["num"] for b in bars or [] if b["num"]] or [1])
        for sb in (self.loop_from, self.loop_to):
            sb.set_range(1, total)
        if self.media:
            self.media.pause()
        self.media = Gtk.MediaFile.new_for_filename(str(wav))
        self.media.set_volume(self.volume.get_value())
        self.media.connect("notify::timestamp", self._tick)
        self.media.connect("notify::duration", self._tick)
        self.media.connect("notify::playing", self._update_icon)
        self.title.set_label(title)
        self.wave.set_filename(str(wave_png) if wave_png else None)
        self.set_visible(True)
        self.set_reveal_child(True)
        self.media.play()

    def loop_range(self):
        """(inizio, fine) in secondi del tratto in loop, None se il loop è spento."""
        if not self.loop_btn.get_active():
            return None
        lo, hi = self.loop_from.get_value_as_int(), self.loop_to.get_value_as_int()
        sel = [b for b in self.strip.bars if b["num"] and lo <= b["num"] <= hi]
        return (sel[0]["start"], sel[-1]["start"] + sel[-1]["dur"]) if sel else None

    def set_loop(self, lo, hi):
        self.loop_from.set_value(lo)
        self.loop_to.set_value(hi)
        self.loop_btn.set_active(True)

    def _loop_changed(self, jump=False):
        rng = self.loop_range()
        if rng and self.media and (jump or not rng[0] <= self.media.get_timestamp() / 1e6 < rng[1]):
            self.media.seek(int(rng[0] * 1e6))
        self.strip.area.queue_draw()
        self.progress.queue_draw()

    def _tick(self, *_a):
        m = self.media
        rng = self.loop_range()
        # fuori dal tratto (fine raggiunta o clic altrove): si torna all'inizio del loop
        if rng and m.get_playing() and not rng[0] - 0.05 <= m.get_timestamp() / 1e6 < rng[1]:
            m.seek(int(rng[0] * 1e6))
        self.time.set_label(fmt_time(m.get_timestamp()))
        self.total.set_label("/ " + fmt_time(m.get_duration()))
        self.progress.queue_draw()
        self.strip.update()
        self._update_pos()

    def _update_pos(self):
        """Battuta e sezione correnti sotto il tempo: "Battuta 7 / 64 · Strofa 3 / 8"."""
        bars = self.strip.bars
        if not bars or not self.media:
            self.pos.set_label("")
            return
        b = bars[self.strip.current(self.media.get_timestamp() / 1e6)]
        total = max((x["num"] for x in bars if x["num"]), default=0)
        if b["num"] is None:
            self.pos.set_label(b["section"].capitalize())
        else:
            self.pos.set_label("Battuta %d / %d · %s %d / %d" % (b["num"], total, b["section"], b["local"], b["size"]))

    def _update_icon(self, *_a):
        playing = self.media is not None and self.media.get_playing()
        self.btn_play.set_icon_name("media-playback-pause-symbolic" if playing else "media-playback-start-symbolic")

    def _draw(self, _area, cr, w, h):
        m = self.media
        frac = m.get_timestamp() / m.get_duration() if m and m.get_duration() else 0
        x = frac * w
        cr.set_source_rgba(0.16, 0.16, 0.21, 0.55)  # parte non ancora suonata più scura
        cr.rectangle(x, 0, w - x, h)
        cr.fill()
        cr.set_source_rgba(0.74, 0.58, 0.98, 0.18)
        cr.rectangle(0, 0, x, h)
        cr.fill()
        dur = m.get_duration() / 1e6 if m and m.get_duration() else 0
        rng = self.loop_range() if dur else None
        if rng:  # tratto in loop: fascia rosa
            cr.set_source_rgba(1.0, 0.47, 0.78, 0.22)
            cr.rectangle(rng[0] / dur * w, 0, (rng[1] - rng[0]) / dur * w, h)
            cr.fill()
        marks = [b for b in self.strip.bars if b["first"] and b["color"] is not None] if dur else []
        for j, b in enumerate(marks):
            bx = b["start"] / dur * w
            col = hex_rgb(SECTION_COLORS[b["color"]])
            cr.set_source_rgba(*col, 0.9)
            cr.rectangle(bx - 1, 0, 2, h)
            cr.fill()
            # nome della sezione accanto al segno, solo se c'è spazio fino al prossimo
            nx = marks[j + 1]["start"] / dur * w if j + 1 < len(marks) else w
            layout = PangoCairo.create_layout(cr)
            layout.set_font_description(Pango.FontDescription.from_string("Sans Bold 7"))
            layout.set_text(b["section"], -1)
            lw = layout.get_pixel_extents()[1].width
            if lw + 8 < nx - bx:
                cr.set_source_rgba(*col, 1)
                cr.move_to(bx + 4, 2)
                PangoCairo.show_layout(cr, layout)
        cr.set_source_rgba(0.97, 0.97, 0.95, 0.9)
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
        self.advanced_widgets = []  # impostazioni nascoste finché non si attiva "Avanzate"
        self.stack.add_titled_with_icon(self._build_song_page(), "song", "Brano", "document-properties-symbolic")
        self.stack.add_titled_with_icon(self._build_sections_page(), "sections", "Sezioni", "view-list-symbolic")
        self.stack.add_titled_with_icon(self._build_yaml_page(), "yaml", "YAML", "text-x-generic-symbolic")

        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)
        logo = Gtk.Image.new_from_icon_name(APP_ID)
        logo.set_pixel_size(28)
        header.pack_start(logo)
        header.pack_start(icon_button("document-open-symbolic", "Apri (Ctrl+O)", self.action_open))
        header.pack_start(icon_button("document-save-symbolic", "Salva (Ctrl+S)", self.action_save))
        # pulsante principale: icona (o rotellina mentre lavora) + testo + scorciatoia
        self.render_btn = Gtk.Button(tooltip_text="Genera l'audio e ascoltalo (Alt+G)", valign=Gtk.Align.CENTER)
        self.render_btn.add_css_class("render-btn")
        inner = Gtk.Box(spacing=8)
        self.spinner = Gtk.Spinner()
        icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.spinner.bind_property("spinning", self.spinner, "visible", GObject.BindingFlags.SYNC_CREATE)
        self.spinner.bind_property("spinning", icon, "visible",
                                   GObject.BindingFlags.SYNC_CREATE | GObject.BindingFlags.INVERT_BOOLEAN)
        self.render_label = Gtk.Label(label="Genera e ascolta")
        keycap = Gtk.Label(label="Alt+G")
        keycap.add_css_class("keycap")
        for w in (self.spinner, icon, self.render_label, keycap):
            inner.append(w)
        self.render_btn.set_child(inner)
        self.render_btn.connect("clicked", lambda _b: self.action_render())
        header.pack_end(self.render_btn)

        self.banner = Adw.Banner(button_label="Installa")
        self.banner.connect("button-clicked", lambda _b: self.install_packs())

        view = Adw.ToolbarView()
        view.add_css_class("bt-main")
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
        bp.add_setter(self.editor_box, "orientation", Gtk.Orientation.VERTICAL)
        bp.add_setter(switcher, "policy", Adw.ViewSwitcherPolicy.NARROW)
        bp.add_setter(self.render_label, "label", "Genera")
        bp.add_setter(keycap, "visible", False)
        # finestra affiancata (es. metà di uno schermo 1366): elenco sezioni a scomparsa, player più corto
        bp.add_setter(self.split, "collapsed", True)
        bp.add_setter(self.player.vol_box, "visible", False)
        bp.add_setter(self.player.folder_btn, "visible", False)
        self.add_breakpoint(bp)
        bp_small = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 600sp"))
        bp_small.add_setter(self.split, "collapsed", True)
        bp_small.add_setter(self.editor_box, "orientation", Gtk.Orientation.VERTICAL)
        bp_small.add_setter(switcher, "policy", Adw.ViewSwitcherPolicy.NARROW)
        bp_small.add_setter(self.render_label, "label", "Genera")
        bp_small.add_setter(keycap, "visible", False)
        bp_small.add_setter(self.player.vol_box, "visible", False)
        bp_small.add_setter(self.player.folder_btn, "visible", False)
        bp_small.add_setter(self.player.loop_box, "visible", False)
        self.add_breakpoint(bp_small)

        self.set_advanced(load_prefs().get("advanced", False))
        self.check_packs()
        if path:
            self.load_file(path)
        else:
            self.load_song(self.song)
            GLib.idle_add(self.offer_draft)

    # ------------------------------------------------------------------ pagina Brano
    def advanced_toggle(self):
        """Pulsante "Avanzate": mostra/nasconde le impostazioni di dettaglio (stato condiviso tra le pagine)."""
        b = Gtk.ToggleButton(action_name="app.advanced", valign=Gtk.Align.CENTER,
                             tooltip_text="Mostra le impostazioni di dettaglio")
        b.set_child(Adw.ButtonContent(icon_name="emblem-system-symbolic", label="Avanzate"))
        b.add_css_class("flat")
        b.add_css_class("adv-toggle")
        return b

    def advanced(self, widget):
        self.advanced_widgets.append(widget)
        return widget

    def set_advanced(self, on):
        for w in self.advanced_widgets:
            w.set_visible(on)
        act = self.get_application().lookup_action("advanced") if self.get_application() else None
        if act and act.get_state().get_boolean() != on:
            act.set_state(GLib.Variant.new_boolean(on))

    def _build_song_page(self):
        page = Adw.PreferencesPage()
        self.w_title = Adw.EntryRow(title="Titolo")
        self.w_tempo = spin_row("Tempo (BPM)", 30, 320, 1, tip="battiti al minuto")
        self.w_groove = GrooveRow("Groove")
        self.w_groove.set_subtitle_lines(1)
        self.w_bass = ChoiceRow("Basso", [("no", "senza basso"), ("contrabbasso", "Rubner 1958 pizzicato"),
                                          ("elettrico", "Black & Blue, a dita"),
                                          ("contrabbasso soft", "Sneakybass, pizzicato leggero")])
        g = group("🎵 Brano", ((self.w_title, "✏️"), (self.w_tempo, "⏱️"), (self.w_groove, "🥁"), (self.w_bass, "🎻")))
        g.set_header_suffix(self.advanced_toggle())
        page.add(g)

        # ordine delle sezioni (ex scheda Arrangiamento)
        self.arr_group = Adw.PreferencesGroup(title="🔁 Ordine delle sezioni")
        self.arr_group.set_tooltip_text("Lista vuota = le sezioni suonano nell'ordine della pagina Sezioni, "
                                        "ognuna con le sue ripetizioni. 'x 0' = ripetizioni della sezione.")
        add = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Aggiungi al fondo", valign=Gtk.Align.CENTER)
        add.add_css_class("flat")
        add.connect("clicked", lambda _b: self.add_arrangement())
        self.arr_group.set_header_suffix(add)
        page.add(self.arr_group)
        self.arr_rows = []

        self.w_guitar = ChoiceRow("Chitarra", [("Gretsch", "Anniversary hollowbody, twang e calore"),
                                               ("Epiphone", "solid body"),
                                               ("Fender", "solid body single coil, per rock e hard rock"),
                                               ("Acustica", "steel string Seagull, senza ampli")])
        self.w_amp = tip(ChoiceRow("Ampli", [("auto", "quello del groove"), ("clean", "pulito"),
                                             ("blues", "leggermente sporco, caldo"), ("twang", "brillante, anni '50"),
                                             ("crunch", "distorsione media"), ("high", "distorsione pesante")]),
                         "auto = quello del groove")
        self.w_double = tip(ChoiceRow("Chitarra doppiata L/R", [("auto", "decide il groove"),
                                                                ("sì", "due chitarre ai lati"),
                                                                ("no", "una chitarra al centro")]),
                            "due chitarre ai lati")
        self.w_voicing = tip(ChoiceRow("Voicing accordi", [("auto", "quello del groove"),
                                                          ("barré", "forma di MI/LA, 5-6 corde"),
                                                          ("aperti", "prima posizione, corde a vuoto"),
                                                          ("jazz", "4 note: tonica, 7a, 3a, 5a"),
                                                          ("triadi", "3 corde alte, suono leggero")]),
                             "come suonare gli accordi pieni (pennate giù/su)")
        self.w_slap = tip(ChoiceRow("Slapback", [("auto", "decide il groove"), ("sì", "eco corta anni '50"),
                                                 ("no", "niente eco")]), "eco corta anni '50")
        page.add(self.advanced(group("🔊 Suono", ((self.w_guitar, "🎸"), (self.w_amp, "📢"),
                                                  (self.w_double, "👯"), (self.w_slap, "📣"),
                                                  (self.w_voicing, "🖐️")))))

        self.w_count = tip(Adw.SwitchRow(title="Conteggio iniziale"), "una battuta di bacchette")
        self.w_ending = tip(Adw.SwitchRow(title="Finale"), "accordo lungo con piatto")
        self.w_end_chord = Adw.EntryRow(title="Accordo finale (vuoto = primo accordo)")
        self.w_fills = tip(Adw.SwitchRow(title="Rullate"), "sull'ultima battuta di ogni sezione")
        self.w_crash = tip(Adw.SwitchRow(title="Piatto sugli attacchi"), "all'inizio di ogni sezione")
        page.add(self.advanced(group("🧱 Struttura", ((self.w_count, "🥢"), (self.w_ending, "🏁"),
                                                      (self.w_end_chord, "🎯"), (self.w_fills, "🥁"),
                                                      (self.w_crash, "💥")))))

        self.w_transpose = spin_row("Trasposizione", -12, 12, 1, tip="semitoni: -1 per accordatura mezzo tono sotto")
        self.w_swing = Adw.ExpanderRow(title="Swing personalizzato")
        self.w_swing.set_tooltip_text("se spento, lo decide il groove")
        self.w_swing.set_show_enable_switch(True)
        self.w_swing_val = spin_row("Swing", 0, 1, 0.05, 2)
        self.w_swing_val.set_subtitle(SWING_HINT)
        self.w_swing.add_row(self.w_swing_val)
        self.w_humanize = spin_row("Umanizzazione", 0, 2, 0.1, 1, "0 = a tempo perfetto, 2 = molto sciolto")
        self.w_strum = spin_row("Velocità pennata (ms)", 0, 40, 1, 0, "millisecondi tra una corda e l'altra")
        self.w_seed = spin_row("Variazione", 1, 9999, 1, 0, "cambia per altre dinamiche e round robin")
        page.add(self.advanced(group("🧑‍🎤 Esecuzione", ((self.w_transpose, "🎹"), (self.w_swing, "🌀"),
                                                        (self.w_humanize, "🫀"), (self.w_strum, "🖐️"),
                                                        (self.w_seed, "🎲")))))

        self.w_outdir = Adw.EntryRow(title="Cartella di output")
        self.w_outdir.set_text("out")
        self.w_mp3 = Adw.SwitchRow(title="Crea anche l'MP3")
        self.w_stems = Adw.SwitchRow(title="Tracce separate (stems)")
        page.add(self.advanced(group("💾 Output", ((self.w_outdir, "📁"), (self.w_mp3, "🎧"), (self.w_stems, "🎚️")))))

        for w in (self.w_title, self.w_end_chord):
            w.connect("changed", self._song_changed)
        for w in (self.w_tempo, self.w_transpose, self.w_swing_val, self.w_humanize, self.w_strum, self.w_seed):
            w.connect("notify::value", self._song_changed)
        for w in (self.w_groove, self.w_guitar, self.w_amp, self.w_double, self.w_slap, self.w_bass, self.w_voicing):
            w.connect("notify::selected", self._song_changed)
        for w in (self.w_count, self.w_ending, self.w_fills, self.w_crash):
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
        s["bass"] = sf.BASSES[self.w_bass.get_selected()]
        s["voicing"] = [None, "barre", "open", "jazz", "triad"][self.w_voicing.get_selected()]
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
    def _build_scales_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_start=18, margin_end=18,
                      margin_top=14, margin_bottom=18)
        title = Gtk.Label(label="🎸 Scale sulla tastiera", xalign=0)
        title.add_css_class("title-2")
        box.append(title)
        scales = list(theory.SCALES)
        self.f_key = GridPicker(sf.KEYS, note_rows(sf.KEYS), fmt=lambda i: "Tonalità: " + sf.KEYS[i])
        self.f_key.set_tooltip_text("La nota di partenza della scala (la «casa»): blues in A = scala di A")
        self.f_key.set_selected(sf.KEYS.index("A"))
        steps = lambda n: " ".join(theory.degree(n, st) for st in theory.SCALES[n]["steps"])
        self.f_scale = MenuRow("Scala", scales, [
            ("🎷  Pentatoniche e blues", scales[:4]), ("🎼  Maggiore e minori", [scales[4], scales[5]] + scales[10:]),
            ("🌈  Modi", scales[6:10])], item_label=lambda n: "%s   %s" % (n, steps(n)), button_label=lambda n: n)
        self.f_scale.set_selected(scales.index("Blues minore"))
        self.f_labels = MenuRow("Etichette", ["Note", "Gradi"], [], top=["Note", "Gradi"],
                                item_label=lambda n: {"Note": "Note — A, C, D…",
                                                      "Gradi": "Gradi — 1, b3, 5…: valgono in ogni tonalità"}[n],
                                button_label=lambda n: "Etichette: " + n)
        # tutte le opzioni su una riga: dei MenuRow si usa solo il pulsante-menu (il valore resta nella riga)
        options = Gtk.Box(spacing=6)
        options.append(self.f_key)
        for row in (self.f_scale, self.f_labels):
            row.remove(row.button)
            row.button.set_tooltip_text(row.get_title())
            options.append(row.button)
        self.f_boxes = ""  # box CAGED selezionati, adiacenti, in ordine lungo il manico ("" = tutti)

        def pick_box(shape):
            self.f_boxes = theory.toggle_box(self.f_boxes, shape) if shape else ""
            sync()
        chips = Gtk.Box(spacing=6)
        lab = Gtk.Label(label="Box CAGED")
        lab.add_css_class("heading")
        lab.set_tooltip_text("Il manico diviso in 5 box, uno per forma d'accordo (C, A, G, E, D). Clic su un box "
                             "per vederlo da solo, poi sui box accanto per allargare la zona; clic su un box "
                             "all'estremità per toglierlo. Puoi cliccare anche le fasce sulla tastiera")
        chips.append(lab)
        self.f_chips = {}
        for c in [""] + list(theory.CAGED):
            b = Gtk.Button(label=c or "Tutti")
            b.add_css_class("chip")
            b.connect("clicked", lambda _b, c=c: pick_box(c))
            chips.append(b)
            self.f_chips[c] = b
        self.f_range = Gtk.Label(xalign=0, hexpand=True, margin_start=6)
        self.f_range.add_css_class("dim-label")
        chips.append(self.f_range)
        self.fretboard = Fretboard(on_box_click=pick_box)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("card")
        card.append(self.fretboard)
        self.f_info = Gtk.Label(xalign=0, wrap=True, use_markup=True)
        self.f_legend = Gtk.Label(xalign=0, wrap=True, use_markup=True)
        self.f_legend.add_css_class("dim-label")
        box.append(options)
        box.append(chips)
        box.append(card)
        box.append(self.f_info)
        box.append(self.f_legend)

        def sync(*_a):
            key = sf.KEYS[self.f_key.get_selected()]
            root = sf.KEYS.index(key)
            scale = scales[self.f_scale.get_selected()]
            self.fretboard.update(root, scale, self.f_boxes, self.f_labels.get_selected() == 1)
            for c, b in self.f_chips.items():
                (b.add_css_class if (c in self.f_boxes if c else not self.f_boxes) else
                 b.remove_css_class)("suggested-action")
            minor = "m" if theory.SCALES[scale]["minor"] else ""
            shown = [(a, b) for sh, a, b in theory.caged_boxes(root, scale) if sh in self.f_boxes]
            self.f_range.set_label(" + ".join(c + minor for c in self.f_boxes) +
                                   ("   tasti %d–%d" % (min(a for a, _ in shown), max(b for _, b in shown))
                                    if shown and len(shown) <= len(self.f_boxes) else "")
                                   if self.f_boxes else "tutto il manico")
            info = theory.SCALES[scale]
            names = theory.scale_names(root, scale)
            notes = "  ".join(names[(root + st) % 12] for st in info["steps"])
            blue = info["blue"]
            kind = "blue note" if scale.startswith("Blues") else "nota caratteristica"
            self.f_info.set_label("<b>%s %s</b>:  %s%s\n<small>%s</small>" % (
                names[root], scale.lower(), notes,
                "   ·   %s <b>%s</b> (%s)" % (kind, names[(root + blue) % 12], theory.degree(scale, blue))
                if blue is not None else "", GLib.markup_escape_text(SCALE_DESC[scale])))
            self.f_legend.set_label(
                "<span foreground='#bd93f9'>●</span> tonica   " +
                ("<span foreground='#ff79c6'>●</span> %s   " % kind if blue is not None else "") +
                "<span foreground='#8be9fd'>●</span> altre note della scala   ·   corda 1 (mi cantino) in alto")
        for w in (self.f_key, self.f_scale, self.f_labels):
            w.connect("notify::selected", sync)
        sync()
        return Gtk.ScrolledWindow(child=box, hscrollbar_policy=Gtk.PolicyType.AUTOMATIC, vexpand=True)

    def _build_sections_page(self):
        self.split = Adw.OverlaySplitView(min_sidebar_width=180, max_sidebar_width=280, sidebar_width_fraction=0.24,
                                          pin_sidebar=True)  # resta visibile dopo un restringimento
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side_head = Gtk.Box(spacing=6, margin_start=14, margin_end=6, margin_top=6)
        side_title = Gtk.Label(label="Sezioni", xalign=0, hexpand=True)
        side_title.add_css_class("heading")
        side_head.append(side_title)
        hide = Gtk.Button(icon_name="go-previous-symbolic", tooltip_text="Chiudi l'elenco delle sezioni (F9)")
        hide.connect("clicked", lambda _b: self.split.set_show_sidebar(False))
        side_head.append(hide)
        side.append(side_head)
        self.sec_list = Gtk.ListBox()
        self.sec_list.add_css_class("navigation-sidebar")
        self.sec_list.connect("row-selected", self._section_selected)
        sc = Gtk.ScrolledWindow(vexpand=True, child=self.sec_list)
        side.append(sc)
        bar = Gtk.Box(spacing=2, margin_start=8, margin_end=8, margin_top=6, margin_bottom=8)
        bar.add_css_class("side-tools")
        add = labeled_button("list-add-symbolic", "Nuova", "Nuova sezione (Ctrl+T)", self.add_section)
        add.remove_css_class("flat")
        add.add_css_class("suggested-action")
        bar.append(add)
        bar.append(icon_button("edit-copy-symbolic", "Duplica sezione (Ctrl+D)", self.duplicate_section))
        bar.append(icon_button("go-up-symbolic", "Sposta su", self.move_section, -1))
        bar.append(icon_button("go-down-symbolic", "Sposta giù", self.move_section, 1))
        bar.append(Gtk.Box(hexpand=True))
        delete = icon_button("user-trash-symbolic", "Elimina sezione", self.delete_section)
        delete.add_css_class("danger")
        bar.append(delete)
        side.append(bar)
        self.split.set_sidebar(side)

        page = Adw.PreferencesPage()
        self.s_name = Adw.EntryRow(title="Nome")
        self.s_repeat = spin_row("Ripetizioni", 1, 64, 1, tip="quante volte suonare questa sezione")
        self.s_groove = GrooveRow("Groove", inherit=True, song_groove=lambda: self.song.get("groove"))
        self.s_groove.set_subtitle_lines(1)
        g = group("🧩 Sezione", ((self.s_name, "🏷️"), (self.s_repeat, "🔁"), (self.s_groove, "🥁")))
        g.set_header_suffix(self.advanced_toggle())
        page.add(g)
        self.s_volume = spin_row("Dinamica", 0.2, 1.5, 0.05, 2, "1 = normale, 0.8 = più piano")
        self.s_swing = Adw.ExpanderRow(title="Swing della sezione")
        self.s_swing.set_show_enable_switch(True)
        self.s_swing_val = spin_row("Swing", 0, 1, 0.05, 2)
        self.s_swing_val.set_subtitle(SWING_HINT)
        self.s_swing.add_row(self.s_swing_val)
        self.s_fill = tip(ChoiceRow("Rullata finale", [("auto", "come il brano"), ("sì", "rullata a fine sezione"),
                                                       ("no", "niente rullata")]), "auto = come il brano")
        self.s_guitar = Adw.SwitchRow(title="Chitarra")
        self.s_drums = Adw.SwitchRow(title="Batteria")
        page.add(self.advanced(group("🎛️ Dettagli", ((self.s_volume, "🔉"), (self.s_swing, "🌀"), (self.s_fill, "🥁"),
                                                      (self.s_guitar, "🎸"), (self.s_drums, "🪘")))))

        chords = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_start=18, margin_end=18,
                         margin_top=14, margin_bottom=18)
        head = Gtk.Box(spacing=8)
        title = Gtk.Label(label="🎼 Accordi", xalign=0)
        title.add_css_class("title-2")
        head.append(title)
        self.bars_info = Gtk.Label(xalign=1, hexpand=True)
        self.bars_info.add_css_class("dim-label")
        hint = help_page([("h", "Una casella = una battuta di 4 tempi"), BAR_EXAMPLES,
                          ("h", "Accordi"), CHORD_EXAMPLES, ("p", "<small>Guida completa: F1</small>")])
        for m in ("start", "end", "top", "bottom"):
            getattr(hint, "set_margin_" + m)(10)
        help_btn = Gtk.MenuButton(icon_name="help-about-symbolic", valign=Gtk.Align.CENTER,
                                  tooltip_text="Come si scrivono battute e accordi", popover=Gtk.Popover(child=hint))
        help_btn.add_css_class("flat")
        help_btn.add_css_class("circular")
        head.insert_child_after(help_btn, title)
        head.append(self.bars_info)
        chords.append(head)
        tools = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tools.add_css_class("card")
        tools.add_css_class("builder")
        quick = Gtk.Box(spacing=6)
        dup = icon_button("edit-copy-symbolic", "Duplica la battuta selezionata (Ctrl+Shift+D)",
                          self.duplicate_focused_bar)
        dup.remove_css_class("flat")
        quick.append(dup)
        for label, tok, hint_text in (("+ %", "%", "ripeti la battuta precedente"), ("+ N.C.", "N.C.", "battuta senza chitarra"),
                                ("+ vuota", "", "battuta da riempire")):
            b = Gtk.Button(label=label, tooltip_text=hint_text)
            b.connect("clicked", lambda _b, t=tok: self.add_bar(t))
            quick.append(b)
        quick.append(Gtk.Box(hexpand=True))
        clear = Gtk.Button(label="Svuota", tooltip_text="Toglie tutte le battute della sezione")
        clear.add_css_class("danger")
        clear.connect("clicked", lambda _b: self.set_bars([]))
        quick.append(clear)
        tools.append(quick)
        chords.append(tools)
        pal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        pal = Gtk.Box(spacing=12)
        pal_label = Gtk.Label(label="🎨 Tavolozza", valign=Gtk.Align.START, margin_top=6)
        pal_label.add_css_class("heading")
        pal_label.set_tooltip_text("Clic = aggiungi alla battuta selezionata · trascina su una battuta per metterlo lì")
        pal.append(pal_label)
        # le 12 note sempre a disposizione (accordo maggiore: m, 7… si aggiungono scrivendo nella battuta),
        # ognuna con la sua alterazione sotto, come nei menu Tonalità
        notes = Gtk.Grid(column_spacing=4, row_spacing=4, valign=Gtk.Align.START)
        for r, row in enumerate(note_rows(sf.KEYS)):
            for c, i in enumerate(row):
                if i is not None:
                    notes.attach(self._palette_chip(sf.KEYS[i]), c, r, 1, 1)
        pal.append(notes)
        pal_box.append(pal)
        used = Gtk.Box(spacing=12)
        used_label = Gtk.Label(label="Usati nel brano", xalign=0, valign=Gtk.Align.START, margin_top=6)
        used_label.add_css_class("dim-label")
        used.append(used_label)
        self.palette = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=20,
                                   column_spacing=4, row_spacing=4, hexpand=True, valign=Gtk.Align.START)
        used.append(self.palette)
        pal_box.append(used)
        chords.append(pal_box)
        self.flow = Gtk.FlowBox(max_children_per_line=4, min_children_per_line=2, homogeneous=True,
                                selection_mode=Gtk.SelectionMode.NONE, column_spacing=4, row_spacing=4,
                                valign=Gtk.Align.START)
        self.flow.add_css_class("bar-grid")
        chords.append(self.flow)
        g = Adw.PreferencesGroup(title="✨ Modelli di giro")
        g.set_tooltip_text("Riempie la sezione con un giro classico")
        self.t_name = deco(MenuRow("Modello", list(sf.TEMPLATES), TEMPLATE_GROUPS, button_label=lambda n: n,
                                   item_label=lambda n: n), "📜")
        self.t_key_sub = lambda *_: self.t_name.set_tooltip_text("| " + " | ".join(
            sf.template_bars(list(sf.TEMPLATES)[self.t_name.get_selected()], sf.KEYS[self.t_key.get_selected()])) + " |")
        self.t_name.label.set_max_width_chars(16)
        self.t_name.label.set_width_chars(10)
        self.t_name.connect("notify::selected", self.t_key_sub)
        self.t_key = deco(PickerRow("Tonalità", GridPicker(sf.KEYS, note_rows(sf.KEYS))), "🔑")
        self.t_key.set_tooltip_text("Tonalità del giro: la nota da cui partono i gradi I, IV, V… "
                                    "(blues in A = A7 D7 E7). Vedi F1 › Tonalità")
        self.t_key.set_selected(sf.KEYS.index("A"))
        self.t_key.connect("notify::selected", self.t_key_sub)
        self.t_key_sub()
        buttons = Gtk.Box(spacing=6, halign=Gtk.Align.END, margin_top=10)
        rep = Gtk.Button(label="Sostituisci accordi",
                         tooltip_text="Cancella le battute della sezione e mette il giro scelto nella tonalità scelta. "
                                      "Non traspone: per cambiare tonalità a un brano usa Trasposizione")
        rep.add_css_class("suggested-action")
        rep.connect("clicked", lambda _b: self.apply_template(replace=True))
        app = Gtk.Button(label="Aggiungi in coda",
                         tooltip_text="Aggiunge il giro dopo le battute che ci sono già")
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
        # colonna centrale a schede: Accordi | Scale (tastiera con le note e il sistema CAGED)
        self.center_stack = Adw.ViewStack(vexpand=True)
        self.center_stack.add_titled_with_icon(chords_scroll, "chords", "Accordi", "view-grid-symbolic")
        self.center_stack.add_titled_with_icon(self._build_scales_page(), "scales", "Scale",
                                               "applications-multimedia-symbolic")
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # riga dei tab: a sinistra riapre l'elenco sezioni (se chiuso), a destra mostra/nasconde le impostazioni
        tabs = Gtk.CenterBox(margin_top=6, margin_start=8, margin_end=8)
        tabs.set_center_widget(Adw.ViewSwitcher(stack=self.center_stack, policy=Adw.ViewSwitcherPolicy.WIDE))
        left = Gtk.Button(valign=Gtk.Align.CENTER, tooltip_text="Mostra l'elenco delle sezioni (F9)")
        left.set_child(Adw.ButtonContent(icon_name="go-next-symbolic", label="Sezioni"))
        left.connect("clicked", lambda _b: self.split.set_show_sidebar(True))
        tabs.set_start_widget(left)
        self.sidebar_toggle = left
        # colonna destra come l'elenco a sinistra: titolo con → che la chiude, «← Impostazioni» la riapre
        self.right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_head = Gtk.Box(spacing=6, margin_start=6, margin_end=14, margin_top=6)
        hide = Gtk.Button(icon_name="go-next-symbolic", tooltip_text="Chiudi le impostazioni (Shift+F9)")
        hide.connect("clicked", lambda _b: self.right_panel.set_visible(False))
        right_head.append(hide)
        right_title = Gtk.Label(label="Impostazioni", xalign=1, hexpand=True)
        right_title.add_css_class("heading")
        right_head.append(right_title)
        self.right_panel.append(right_head)
        page.set_vexpand(True)
        self.right_panel.append(page)
        show = Gtk.Button(valign=Gtk.Align.CENTER, tooltip_text="Mostra le impostazioni della sezione (Shift+F9)")
        show.set_child(Adw.ButtonContent(icon_name="go-previous-symbolic", label="Impostazioni"))
        show.connect("clicked", lambda _b: self.right_panel.set_visible(True))
        self.right_panel.bind_property("visible", show, "visible",
                                       GObject.BindingFlags.INVERT_BOOLEAN | GObject.BindingFlags.SYNC_CREATE)
        tabs.set_end_widget(show)
        center.append(tabs)
        center.append(self.center_stack)
        # divisore trascinabile: lo spazio in più va agli accordi, le impostazioni restano almeno 440 px
        self.editor_box = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, wide_handle=True,
                                    start_child=center, end_child=self.right_panel,
                                    resize_start_child=True, resize_end_child=False,
                                    shrink_start_child=False, shrink_end_child=False)
        self.sec_stack.add_named(self.editor_box, "editor")
        self.sec_stack.add_named(empty, "empty")
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # elenco chiuso (con ‹ in cima all'elenco, F9 o finestra stretta): «Sezioni ›» nella riga dei tab lo riapre
        self.split.set_show_sidebar(True)
        self.split.bind_property("show-sidebar", self.sidebar_toggle, "visible",
                                 GObject.BindingFlags.INVERT_BOOLEAN | GObject.BindingFlags.SYNC_CREATE)
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
            row.emoji = Gtk.Label(label=style_emoji(sec["groove"] or self.song["groove"]),
                                  tooltip_text=sec["groove"] or "groove del brano")
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
        parts = ["×%d" % sec["repeat"], "%d batt." % len(sec["bars"])]
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
            card = BarCell(self, i, text, color, len(str(n)))
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
        """Accordi già usati nel brano (le 12 note sono fisse, accanto)."""
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
            self.palette.append(self._palette_chip(tok))

    def _palette_chip(self, chord):
        chip = Gtk.Button(label=chord, tooltip_text="Clic: aggiungi alla battuta selezionata · trascina su una battuta")
        chip.add_css_class("chip")
        chip.connect("clicked", lambda _b: self.append_to_focused(chord))
        drag_source(chip, lambda: "chord:" + chord)
        return chip

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

    def remove_focused_bar(self):
        sec = self.section
        i = self.focused_bar
        if not sec or i is None or i >= len(sec["bars"]):
            self.toast("Seleziona prima una battuta")
            return
        self.remove_bar(i)

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
    def rebuild_arrangement(self):
        for row in self.arr_rows:
            self.arr_group.remove(row)
        self.arr_rows = []
        names = [s["name"] for s in self.song["sections"]]
        if not self.song["arrangement"]:
            row = Adw.ActionRow(title="Automatico", subtitle_lines=2,
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
        self.w_voicing.set_selected([None, "barre", "open", "jazz", "triad"].index(s.get("voicing"))
                                    if s.get("voicing") in ("barre", "open", "jazz", "triad") else 0)
        self.w_bass.set_selected(sf.BASSES.index(s["bass"]) if s["bass"] in sf.BASSES else (1 if s["bass"] else 0))
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
            self.arr_group.set_description(None)
        else:
            try:
                order, timeline = build_timeline(sf.to_song_dict(self.song))
                bars = len(timeline) + (1 if self.song["count_in"] else 0) + (2 if self.song["ending"] else 0)
                secs = bars * 4 * 60 / self.song["tempo"]
                info = "%d battute · %d:%02d" % (len(timeline), secs // 60, secs % 60)
                self.arr_group.set_description(info)
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
            examples = EXAMPLES
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
        try:
            bass = packs.bass_pack(self.song.get("bass"))
        except SongError:
            bass = None
        if bass:
            need.append(bass)
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

        shown = [None]

        def progress(name, done, total, _files=None):
            mb = "%d / %d MB" % (done >> 20, total >> 20) if total else "%d MB" % (done >> 20)
            title = "Scarico i campioni: %s%s · %s" % (name, " %d%%" % (100 * done // total) if total else "", mb)
            if title != shown[0]:  # una chiamata per blocco scaricato: aggiorna solo se cambia
                shown[0] = title
                GLib.idle_add(self.banner.set_title, title)

        def work():
            try:
                for p in missing:
                    packs.install(p, progress=lambda d, t, f=None, p=p: progress(p, d, t, f))
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

    def action_help(self):
        stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, hexpand=True)
        for title, icon, items in HELP:
            page = help_page(items)
            head = Gtk.Label(label="%s  %s" % (icon, title), xalign=0)
            head.add_css_class("title-1")
            page.prepend(head)
            clamp = Adw.Clamp(child=page, maximum_size=620, margin_start=24, margin_end=24, margin_top=18,
                              margin_bottom=24)
            stack.add_titled(Gtk.ScrolledWindow(child=clamp, hscrollbar_policy=Gtk.PolicyType.NEVER),
                             title, "%s  %s" % (icon, title))
        side = Gtk.StackSidebar(stack=stack)
        side.add_css_class("help-side")
        body = Gtk.Box()
        body.append(side)
        body.append(stack)
        view = Adw.ToolbarView(content=body)
        view.add_top_bar(Adw.HeaderBar())
        Adw.Dialog(title="Guida", child=view, content_width=860, content_height=640).present(self)

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
                  Gdk.KEY_s: self.play_stop, Gdk.KEY_S: self.play_stop,
                  Gdk.KEY_l: self.play_loop, Gdk.KEY_L: self.play_loop}.get(keyval)
        if action:
            action()
            return True
        return False

    def _ready(self):
        if self.player.media is None:
            self.toast("Niente da suonare: premi Genera e ascolta (Alt+G)")
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

    def play_loop(self):
        if self._ready():
            self.player.loop_btn.set_active(not self.player.loop_btn.get_active())

    def open_output_dir(self):
        wav = getattr(self, "last_output", None)
        if wav:
            Gtk.FileLauncher.new(Gio.File.new_for_path(str(Path(wav).resolve()))).open_containing_folder(
                self, None, None)


# installato: dentro il pacchetto; da sorgente: la cartella examples/ del repo
EXAMPLES = next((d for d in (Path(__file__).resolve().parent / "examples",
                             Path(__file__).resolve().parent.parent / "examples") if d.is_dir()),
                Path(__file__).resolve().parent / "examples")
DRAFT = packs.data_dir() / "bozza.json"
PREFS = packs.data_dir() / "gui.json"


def load_prefs():
    """Preferenze dell'editor (per ora: impostazioni avanzate visibili sì/no)."""
    import json
    try:
        return json.loads(PREFS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_prefs(**kw):
    import json
    prefs = load_prefs()
    prefs.update(kw)
    try:
        PREFS.parent.mkdir(parents=True, exist_ok=True)
        PREFS.write_text(json.dumps(prefs), encoding="utf-8")
    except OSError:
        pass


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
    part.append("Elimina battuta", "app.bar-del")
    sec_menu.append_section(None, part)
    menubar.append_submenu("_Sezione", sec_menu)

    play_menu = Gio.Menu()
    for label, action, accel in (("Play / pausa", "app.play-toggle", "space"), ("Da capo", "app.play-restart", "b"),
                                 ("Stop", "app.play-stop", "s"),
                                 ("Loop", "app.play-loop", "l")):
        item = Gio.MenuItem.new(label, action)
        item.set_attribute_value("accel", GLib.Variant.new_string(accel))  # solo indicazione: gestite dal tasto
        play_menu.append_item(item)

    song_menu = Gio.Menu()
    song_menu.append("Genera e ascolta", "app.render")
    song_menu.append("Impostazioni avanzate", "app.advanced")
    song_menu.append("Apri cartella output", "app.open-output")
    song_menu.append("Installa campioni mancanti", "app.install")
    menubar.append_submenu("_Brano", song_menu)
    menubar.append_submenu("_Riproduzione", play_menu)

    help_menu = Gio.Menu()
    help_menu.append("Guida", "app.guide")
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
                        "aformat=channel_layouts=mono,showwavespic=s=1600x120:colors=#bd93f9:scale=lin",
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
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)  # Dracula è solo scuro
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        # sopra il gtk.css dell'utente: temi come Arc ridipingono di blu suggested-action e gli slider
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)
        win = MainWindow(self, self.path)
        for name, accel, fn in (("new", "<Control>n", win.action_new), ("open", "<Control>o", win.action_open),
                                ("save", "<Control>s", win.action_save),
                                ("save-as", "<Control><Shift>s", win.action_save_as),
                                ("render", "<Alt>g", win.action_render),
                                ("section-new", "<Control>t", win.add_section),
                                ("section-dup", "<Control>d", win.duplicate_section),
                                ("bar-new", "<Control>b", lambda: win.add_bar("")),
                                ("bar-dup", "<Control><Shift>d", win.duplicate_focused_bar),
                                ("bar-del", "<Super>Delete", win.remove_focused_bar),
                                ("guide", "F1", win.action_help),
                                ("sidebar", "F9", lambda: win.split.set_show_sidebar(not win.split.get_show_sidebar())),
                                ("settings-panel", "<Shift>F9", lambda: win.right_panel.set_visible(
                                    not win.right_panel.get_visible())),
                                ("quit", "<Control>q", win.close)):
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", lambda _a, _p, f=fn: f())
            self.add_action(act)
            self.set_accels_for_action("app." + name, [accel])
        self.set_accels_for_action("app.render", ["<Alt>g", "<Control>r"])
        self.set_accels_for_action("app.bar-new", ["<Control>b", "<Super>n"])
        adv = Gio.SimpleAction.new_stateful("advanced", None, GLib.Variant.new_boolean(False))

        def on_adv(a, value):
            a.set_state(value)
            win.set_advanced(value.get_boolean())
            save_prefs(advanced=value.get_boolean())
        adv.connect("change-state", on_adv)
        self.add_action(adv)
        win.set_advanced(load_prefs().get("advanced", False))
        for name, fn in (("open-output", win.open_output_dir), ("install", win.install_packs),
                         ("section-del", win.delete_section), ("play-toggle", win.play_toggle),
                         ("play-restart", win.play_restart), ("play-stop", win.play_stop), ("play-loop", win.play_loop), ("section-up", lambda: win.move_section(-1)),
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
