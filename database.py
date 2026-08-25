import os
import uuid
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")


def create_connection():
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def get_cursor(commit=False):
    """Opens a connection/cursor, always closes the connection afterward
    (even if an error happens), and commits only if commit=True."""
    connection = create_connection()
    try:
        cursor = connection.cursor()
        yield cursor
        if commit:
            connection.commit()
    finally:
        connection.close()


def create_table():
    with get_cursor(commit=True) as cursor:
        # 1. Readings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id SERIAL PRIMARY KEY,
                user_name TEXT,
                category TEXT,
                card_name TEXT,
                meaning TEXT,
                orientation TEXT,
                group_id TEXT,
                note_text TEXT,
                note_image TEXT,
                note_image_position INTEGER,
                question TEXT,
                ai_response TEXT,
                target_name TEXT
            )
        """)

        new_columns = {
            "group_id": "TEXT",
            "note_text": "TEXT",
            "note_image": "TEXT",
            "note_image_position": "INTEGER",
            "question": "TEXT",
            "ai_response": "TEXT",
            "target_name": "TEXT",
            "created_at": "TIMESTAMP DEFAULT NOW()",
            "image_filename": "TEXT",
        }
        for column_name, column_type in new_columns.items():
            cursor.execute(f"ALTER TABLE readings ADD COLUMN IF NOT EXISTS {column_name} {column_type}")

        # 2. Oracle Stories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oracle_stories (
                id SERIAL PRIMARY KEY,
                user_name TEXT NOT NULL,
                group_id TEXT NOT NULL,
                story TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # 3. Translation Cache Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_cache (
                text TEXT,
                lang TEXT,
                translated TEXT,
                PRIMARY KEY (text, lang)
            )
        """)


def save_reading_full(user_name, category, card_name, meaning, orientation, group_id=None,
                       question=None, ai_response=None, target_name=None, image_filename=None):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO readings (user_name, category, card_name, meaning, orientation, group_id,
                                   question, ai_response, target_name, image_filename)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_name, category, card_name, meaning, orientation, group_id,
              question, ai_response, target_name, image_filename))
        return cursor.fetchone()[0]


def get_two_person_groups(user_name):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT group_id FROM readings
            WHERE user_name = %s AND category = 'two_person' AND group_id IS NOT NULL
            ORDER BY group_id DESC
        """, (user_name,))
        group_ids = [row[0] for row in cursor.fetchall()]

        groups = []
        for gid in group_ids:
            cursor.execute("""
                SELECT id, category, card_name, meaning, orientation, note_text, note_image, note_image_position, question, ai_response, target_name, group_id
                FROM readings
                WHERE user_name = %s AND group_id = %s
                ORDER BY id
            """, (user_name, gid))
            rows = cursor.fetchall()
            if len(rows) >= 2:
                groups.append({
                    "group_id": gid,
                    "person1": rows[0],
                    "person2": rows[1],
                    "story": rows[0][9],   # ai_response is now index 9
                    "names": rows[0][8],   # question is now index 8
                })
        return groups


def new_group_id():
    return uuid.uuid4().hex[:8]


def save_reading(user_name, category, card_name, meaning, orientation, group_id=None):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO readings (user_name, category, card_name, meaning, orientation, group_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_name, category, card_name, meaning, orientation, group_id))
        return cursor.fetchone()[0]


def save_oracle_story(user_name, group_id, story):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO oracle_stories (user_name, group_id, story)
            VALUES (%s, %s, %s)
        """, (user_name, group_id, story))


def get_readings(user_name, category):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position, question, ai_response
            FROM readings
            WHERE user_name = %s AND category = %s
            ORDER BY id DESC
        """, (user_name, category))
        return cursor.fetchall()


def get_reading_by_id(reading_id, user_name):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, category, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position
            FROM readings
            WHERE id = %s AND user_name = %s
        """, (reading_id, user_name))
        return cursor.fetchone()


def save_note(reading_id, user_name, note_text, note_image, note_image_position):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE readings
            SET note_text = %s, note_image = %s, note_image_position = %s
            WHERE id = %s AND user_name = %s
        """, (note_text, note_image, note_image_position, reading_id, user_name))


def get_oracle_groups(user_name):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT group_id FROM readings
            WHERE user_name = %s AND group_id IS NOT NULL
            ORDER BY group_id DESC
        """, (user_name,))
        group_ids = [row[0] for row in cursor.fetchall()]

        groups = []
        for group_id in group_ids:
            cursor.execute("""
                SELECT id, category, card_name, meaning, orientation, note_text, note_image, note_image_position
                FROM readings
                WHERE user_name = %s AND group_id = %s
            """, (user_name, group_id))
            card_rows = cursor.fetchall()
            cards_by_category = {row[1]: row for row in card_rows}

            cursor.execute("""
                SELECT story FROM oracle_stories
                WHERE user_name = %s AND group_id = %s
            """, (user_name, group_id))
            story_row = cursor.fetchone()
            story = story_row[0] if story_row else None

            groups.append({
                "group_id": group_id,
                "past": cards_by_category.get("past"),
                "present": cards_by_category.get("present"),
                "future": cards_by_category.get("future"),
                "story": story,
            })

        return groups


def limit_readings(user_name, category, max_rows):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            DELETE FROM readings
            WHERE user_name = %s AND category = %s
            AND id NOT IN (
                SELECT id FROM readings
                WHERE user_name = %s AND category = %s
                ORDER BY id DESC
                LIMIT %s
            )
        """, (user_name, category, user_name, category, max_rows))


def get_cached_translation(text, lang):
    with get_cursor() as cursor:
        cursor.execute("SELECT translated FROM translation_cache WHERE text = %s AND lang = %s", (text, lang))
        row = cursor.fetchone()
        return row[0] if row else None


def save_cached_translation(text, lang, translated):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO translation_cache (text, lang, translated)
            VALUES (%s, %s, %s)
            ON CONFLICT (text, lang) DO UPDATE SET translated = EXCLUDED.translated
        """, (text, lang, translated))


def get_calendar_predictions(user_name):
    """Returns predictions grouped by calendar day (date -> list of prediction dicts).
    Oracle draws (3 cards) and Two-person predictions (2 cards) are folded into a
    single prediction dict each, since they share a group_id — so the Calendar page
    shows one square per prediction, not one square per card."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, category, card_name, meaning, orientation, group_id,
                   question, ai_response, target_name, image_filename, created_at
            FROM readings
            WHERE user_name = %s
            ORDER BY created_at DESC, id ASC
        """, (user_name,))
        rows = cursor.fetchall()

        cursor.execute("""
            SELECT group_id, story FROM oracle_stories WHERE user_name = %s
        """, (user_name,))
        oracle_stories = {row[0]: row[1] for row in cursor.fetchall()}

    seen_group_ids = set()
    predictions = []

    for row in rows:
        (reading_id, category, card_name, meaning, orientation, group_id,
         question, ai_response, target_name, image_filename, created_at) = row

        if group_id and group_id in seen_group_ids:
            continue

        if group_id and category in ("past", "present", "future"):
            seen_group_ids.add(group_id)
            siblings = [r for r in rows if r[5] == group_id]
            cards = [
                {"label": r[1], "card_name": r[2], "meaning": r[3], "orientation": r[4], "image_filename": r[9]}
                for r in siblings
            ]
            predictions.append({
                "type": "oracle",
                "id": reading_id,
                "cards": cards,
                "ai_response": oracle_stories.get(group_id),
                "created_at": created_at,
            })

        elif group_id and category == "two_person":
            seen_group_ids.add(group_id)
            siblings = [r for r in rows if r[5] == group_id]
            cards = [
                {"card_name": r[2], "meaning": r[3], "orientation": r[4], "image_filename": r[9], "target_name": r[8]}
                for r in siblings
            ]
            predictions.append({
                "type": "two_person",
                "id": reading_id,
                "cards": cards,
                "ai_response": siblings[0][7] if siblings else None,
                "created_at": created_at,
            })

        elif category in ("past", "present", "future"):
            predictions.append({
                "type": "single",
                "id": reading_id,
                "category": category,
                "cards": [{"card_name": card_name, "meaning": meaning, "orientation": orientation, "image_filename": image_filename}],
                "created_at": created_at,
            })

        elif category == "question":
            predictions.append({
                "type": "question",
                "id": reading_id,
                "cards": [{"card_name": card_name, "meaning": meaning, "orientation": orientation, "image_filename": image_filename}],
                "question": question,
                "ai_response": ai_response,
                "created_at": created_at,
            })

        elif category == "yes_no":
            predictions.append({
                "type": "yes_no",
                "id": reading_id,
                "question": question,
                "ai_response": ai_response,
                "created_at": created_at,
            })

# Group predictions into: { "Month Year": { "Day Month Year": [pred1, pred2, ...] } }
    calendar_data = {}
    for pred in predictions:
        dt = pred.get("created_at")
        if not dt:
            continue
            
        month_label = dt.strftime("%B %Y")  # e.g., "August 2026"
        day_num = dt.strftime("%d %B %Y")   # e.g., "25 August 2026"

        if month_label not in calendar_data:
            calendar_data[month_label] = {}

        if day_num not in calendar_data[month_label]:
            calendar_data[month_label][day_num] = []

        calendar_data[month_label][day_num].append(pred)

    return calendar_data

def get_calendar_data(user_name):
    """Bridge function that returns predictions structured for calendar.html"""
    return get_calendar_predictions(user_name)


def get_user_calendar(user_name):
    """Fetches and structures calendar data for the specified user."""
    return get_calendar_predictions(user_name)