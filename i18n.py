import os
from flask import session
import database as Tarot_database
from translations import TRANSLATIONS
from deep_translator import GoogleTranslator

TRANSLATOR_EMAIL = os.getenv("TRANSLATOR_EMAIL")


def t(key):
    lang = session.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


LANG_CODE_MAP = {"en": "en", "he": "he", "uk": "uk"}

_translation_cache = {}


import time

def translate_meaning(text, lang):
    if lang == "en":
        return text

    cached = Tarot_database.get_cached_translation(text, lang)
    if cached:
        return cached

    try:
        target = LANG_CODE_MAP.get(lang, lang)
        translated = GoogleTranslator(source="auto", target=target).translate(text)
        time.sleep(0.5)  # small pause to avoid tripping rate limits

        if not translated or "Error 500" in translated or "Server Error" in translated or len(translated) > len(text) * 4:
            print("TRANSLATE REJECTED RESULT:", translated, flush=True)
            return text

        Tarot_database.save_cached_translation(text, lang, translated)
        return translated
    except Exception as error:
        print("TRANSLATE FAILED:", repr(error), flush=True)
        return text 


def tr(text):
    return translate_meaning(text, session.get("lang", "en"))