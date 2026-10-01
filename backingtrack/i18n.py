"""Lingua dei testi: nel codice sono scritti in italiano, le traduzioni inglesi stanno in locale_en.py.

Uso: `from .i18n import _` e `_("testo italiano")`. Le costanti di modulo (guida, descrizioni…) restano in
italiano e si traducono dove vengono mostrate, così il cambio di lingua non dipende dall'ordine degli import.
Lingua: set_lang() (preferenza della GUI), altrimenti BACKINGTRACK_LANG, altrimenti quella del sistema.
"""
import locale
import os

LANGS = {"it": "Italiano", "en": "English"}
_lang = None


def system_lang():
    for var in ("BACKINGTRACK_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "")
        if value:
            return "it" if value.lower().startswith("it") else "en"
    code = (locale.getlocale()[0] or "").lower()
    return "it" if code.startswith("it") else "en"


def lang():
    global _lang
    if _lang is None:
        _lang = system_lang()
    return _lang


def set_lang(code):
    global _lang
    _lang = code if code in LANGS else system_lang()


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
