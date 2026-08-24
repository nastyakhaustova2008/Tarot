import sqlite3
import uuid
from contextlib import contextmanager


def create_connection():
    connection = sqlite3.connect("taro.db")
    return connection


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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(readings)").fetchall()]
        new_columns = {
            "group_id": "TEXT",
            "note_text": "TEXT",
            "note_image": "TEXT",
            "note_image_position": "INTEGER",
            "question": "TEXT",
            "ai_response": "TEXT",
            "target_name": "TEXT",
        }
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE readings ADD COLUMN {column_name} {column_type}")

        # 2. Oracle Stories Table (Fixes the missing table error)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oracle_stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                group_id TEXT NOT NULL,
                story TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Translation Cache Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS translation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT UNIQUE,
                lang TEXT,
                translated_text TEXT
            )
        """)


def save_reading_full(user_name, category, card_name, meaning, orientation, group_id=None, question=None, ai_response=None, target_name=None):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO readings (user_name, category, card_name, meaning, orientation, group_id, question, ai_response, target_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_name, category, card_name, meaning, orientation, group_id, question, ai_response, target_name))
        return cursor.lastrowid


def get_two_person_groups(user_name):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT group_id FROM readings
            WHERE user_name = ? AND category = 'two_person' AND group_id IS NOT NULL
            ORDER BY id DESC
        """, (user_name,))
        group_ids = [row[0] for row in cursor.fetchall()]

        groups = []
        for gid in group_ids:
            cursor.execute("""
                SELECT id, category, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position, question, ai_response, target_name
                FROM readings
                WHERE user_name = ? AND group_id = ?
            """, (user_name, gid))
            rows = cursor.fetchall()
            if len(rows) >= 2:
                groups.append({
                    "group_id": gid,
                    "person1": rows[0],
                    "person2": rows[1],
                    "story": rows[0][10],  # ai_response
                    "names": rows[0][9],   # question field holds "Name1 & Name2"
                })
        return groups


def new_group_id():
    """Generate a short unique id used to link a past+present+future+story set together."""
    return uuid.uuid4().hex[:8]


def save_reading(user_name, category, card_name, meaning, orientation, group_id=None):
    """Saves a reading. group_id is optional — pass it only when this card is part of
    an Oracle draw, so it can be linked to its two sibling cards and the AI story."""
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO readings (user_name, category, card_name, meaning, orientation, group_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_name, category, card_name, meaning, orientation, group_id))
        return cursor.lastrowid


def save_oracle_story(user_name, group_id, story):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT INTO oracle_stories (user_name, group_id, story)
            VALUES (?, ?, ?)
        """, (user_name, group_id, story))


def get_readings(user_name, category):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position, question, ai_response
            FROM readings
            WHERE user_name = ? AND category = ?
            ORDER BY id DESC
        """, (user_name, category))
        return cursor.fetchall()


def get_reading_by_id(reading_id, user_name):
    """Fetches one specific reading, used when opening the note editor.
    Checking user_name too prevents one user from editing another user's reading."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT id, category, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position
            FROM readings
            WHERE id = ? AND user_name = ?
        """, (reading_id, user_name))
        return cursor.fetchone()


def save_note(reading_id, user_name, note_text, note_image, note_image_position):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            UPDATE readings
            SET note_text = ?, note_image = ?, note_image_position = ?
            WHERE id = ? AND user_name = ?
        """, (note_text, note_image, note_image_position, reading_id, user_name))


def get_oracle_groups(user_name):
    """Returns every past Oracle draw for this user as a grouped bundle:
    its past/present/future cards plus the AI story, all linked by group_id."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT group_id FROM readings
            WHERE user_name = ? AND group_id IS NOT NULL
            ORDER BY id DESC
        """, (user_name,))
        group_ids = [row[0] for row in cursor.fetchall()]

        groups = []
        for group_id in group_ids:
            cursor.execute("""
                SELECT id, category, card_name, meaning, orientation, note_text, note_image, note_image_position
                FROM readings
                WHERE user_name = ? AND group_id = ?
            """, (user_name, group_id))
            card_rows = cursor.fetchall()
            cards_by_category = {row[1]: row for row in card_rows}

            cursor.execute("""
                SELECT story FROM oracle_stories
                WHERE user_name = ? AND group_id = ?
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
            WHERE user_name = ? AND category = ?
            AND id NOT IN (
                SELECT id FROM readings
                WHERE user_name = ? AND category = ?
                ORDER BY id DESC
                LIMIT ?
            )
        """, (user_name, category, user_name, category, max_rows))


def create_translation_cache_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translation_cache (
            text TEXT,
            lang TEXT,
            translated TEXT,
            PRIMARY KEY (text, lang)
        )
    """)


def get_cached_translation(text, lang):
    with get_cursor() as cursor:
        cursor.execute("SELECT translated FROM translation_cache WHERE text = ? AND lang = ?", (text, lang))
        row = cursor.fetchone()
        return row[0] if row else None


def save_cached_translation(text, lang, translated):
    with get_cursor(commit=True) as cursor:
        cursor.execute("""
            INSERT OR REPLACE INTO translation_cache (text, lang, translated)
            VALUES (?, ?, ?)
        """, (text, lang, translated))