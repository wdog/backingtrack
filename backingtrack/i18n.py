"""Lingua dei testi: nel codice sono scritti in italiano, le traduzioni inglesi stanno in locale_en.py.

Uso: `from .i18n import _` e `_("testo italiano")`. Le costanti di modulo (guida, descrizioni…) restano in
italiano e si traducono dove vengono mostrate, così il cambio di lingua non dipende dall'ordine degli import.
Lingua: set_lang() (preferenza della GUI), altrimenti BACKINGTRACK_LANG, altrimenti inglese.
"""
import os

LANGS = {"it": "Italiano", "en": "English"}
_lang = None


def default_lang():
    """Inglese, salvo BACKINGTRACK_LANG=it (la GUI ricorda poi la scelta fatta dal menu)."""
    value = os.environ.get("BACKINGTRACK_LANG", "").lower()
    return "it" if value.startswith("it") else "en"


def lang():
    global _lang
    if _lang is None:
        _lang = default_lang()
    return _lang


def set_lang(code):
    global _lang
    _lang = code if code in LANGS else default_lang()


def _(text):
    if lang() == "it" or not text:
        return text
    from .locale_en import EN
    return EN.get(text, text)


def groove_desc(name, desc):
    """Descrizione di un groove nella lingua corrente."""
    if lang() == "it":
        return desc
    from .locale_en import GROOVES_EN
    return GROOVES_EN.get(name, desc)
