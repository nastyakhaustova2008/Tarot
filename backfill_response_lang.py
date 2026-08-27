"""
One-time migration: for existing rows where response_lang is NULL
(readings.ai_response and oracle_stories.story saved before the
response_lang column existed), guess the language by looking at
which alphabet the text uses, and fill it in.

Run once:
    python backfill_response_lang.py
"""

import re
from database import get_cursor

HEBREW_RE = re.compile(r'[\u0590-\u05FF]')
CYRILLIC_RE = re.compile(r'[\u0400-\u04FF]')


def guess_lang(text):
    if not text:
        return "en"
    if HEBREW_RE.search(text):
        return "he"
    if CYRILLIC_RE.search(text):
        return "uk"
    return "en"


def backfill():
    updated_readings = 0
    updated_stories = 0

    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT id, ai_response FROM readings
            WHERE response_lang IS NULL AND ai_response IS NOT NULL
        """)
        rows = cursor.fetchall()
        for reading_id, ai_response in rows:
            lang = guess_lang(ai_response)
            cursor.execute(
                "UPDATE readings SET response_lang = %s WHERE id = %s",
                (lang, reading_id)
            )
            updated_readings += 1

        cursor.execute("""
            SELECT id, story FROM oracle_stories
            WHERE response_lang IS NULL AND story IS NOT NULL
        """)
        rows = cursor.fetchall()
        for story_id, story in rows:
            lang = guess_lang(story)
            cursor.execute(
                "UPDATE oracle_stories SET response_lang = %s WHERE id = %s",
                (lang, story_id)
            )
            updated_stories += 1

    print(f"Updated {updated_readings} rows in readings")
    print(f"Updated {updated_stories} rows in oracle_stories")


if __name__ == "__main__":
    backfill()