"""Translation loading + RTL-aware string lookup."""
import json
import locale
import functools
from fitfusion.config import DATA_DIR, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

import streamlit as st


@functools.lru_cache(maxsize=None)
def _load(lang: str) -> dict:
    path = DATA_DIR / "translations" / f"{lang}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_language() -> str:
    """Best-effort detection of the OS/browser language. Falls back to English."""
    try:
        sys_locale = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    except Exception:
        sys_locale = ""
    sys_locale = (sys_locale or "").lower()
    for code in SUPPORTED_LANGUAGES:
        if sys_locale.startswith(code):
            return code
    return DEFAULT_LANGUAGE


def current_language() -> str:
    if "language" not in st.session_state:
        st.session_state["language"] = detect_language()
    return st.session_state["language"]


def set_language(lang: str) -> None:
    if lang in SUPPORTED_LANGUAGES:
        st.session_state["language"] = lang


def is_rtl() -> bool:
    return SUPPORTED_LANGUAGES[current_language()]["dir"] == "rtl"


def t(key: str, **kwargs) -> str:
    """Translate `key` into the current session language, with optional {placeholders}."""
    lang = current_language()
    strings = _load(lang)
    text = strings.get(key) or _load(DEFAULT_LANGUAGE).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
