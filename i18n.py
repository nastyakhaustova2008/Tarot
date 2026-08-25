import os
import time
from flask import session
from deep_translator import GoogleTranslator
import database as Tarot_database
from translations import TRANSLATIONS

# Correct ISO 639-1 language codes for Google Translator
LANG_CODE_MAP = {
    "en": "en",
    "he": "he",
    "uk": "uk"
}

_memory_cache = {}

def t(key):
    lang = session.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {})).get(key, key)

def translate_meaning(text, lang=None):
    if not text or not isinstance(text, str):
        return "" if text is None else str(text)

    if lang is None:
        lang = session.get("lang", "en")

    if lang == "en":
        return text

    target_lang = LANG_CODE_MAP.get(lang, lang)

    # Check cache first
    try:
        cached = Tarot_database.get_cached_translation(text, target_lang)
        if cached:
            return cached
    except Exception as db_err:
        print(f"CACHE READ FAILED: {repr(db_err)}", flush=True)

    # Request live translation
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)

        if not translated or "Error 500" in translated or "Server Error" in translated:
            return text

        # Attempt to save to cache, proceed even if DB save fails
        try:
            Tarot_database.save_cached_translation(text, target_lang, translated)
        except Exception:
            pass

        return translated

    except Exception as error:
        print(f"TRANSLATE FAILED: {repr(error)}", flush=True)
        return text

def tr(text):
    # If the text is a key in dictionary, use dictionary translation first
    translated_dict = t(text)
    if translated_dict != text:
        return translated_dict

    return translate_meaning(text, session.get("lang", "en"))