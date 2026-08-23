import sqlite3
import uuid


def create_connection():
    connection = sqlite3.connect("taro.db")
    return connection


def create_table():
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            category TEXT,
            card_name TEXT,
            meaning TEXT,
            orientation TEXT
        )
    """)

    # Migration: add new columns if this is an older database that doesn't have them yet.
    # Safe to run every time the app starts — it only adds columns that are missing.
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(readings)").fetchall()]
    new_columns = {
        "group_id": "TEXT",
        "note_text": "TEXT",
        "note_image": "TEXT",
        "note_image_position": "INTEGER",
    }
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE readings ADD COLUMN {column_name} {column_type}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oracle_stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            group_id TEXT,
            story TEXT
        )
    """)

    connection.commit()
    connection.close()


def new_group_id():
    """Generate a short unique id used to link a past+present+future+story set together."""
    return uuid.uuid4().hex[:8]


def save_reading(user_name, category, card_name, meaning, orientation, group_id=None):
    """Saves a reading. group_id is optional — pass it only when this card is part of
    an Oracle draw, so it can be linked to its two sibling cards and the AI story."""
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO readings (user_name, category, card_name, meaning, orientation, group_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_name, category, card_name, meaning, orientation, group_id))
    connection.commit()
    new_id = cursor.lastrowid
    connection.close()
    return new_id


def save_oracle_story(user_name, group_id, story):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO oracle_stories (user_name, group_id, story)
        VALUES (?, ?, ?)
    """, (user_name, group_id, story))
    connection.commit()
    connection.close()


def get_readings(user_name, category):
    """Returns readings for a single category (past, present, or future),
    newest first, including note and group info for the history page."""
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position
        FROM readings
        WHERE user_name = ? AND category = ?
        ORDER BY id DESC
    """, (user_name, category))
    rows = cursor.fetchall()
    connection.close()
    return rows


def get_reading_by_id(reading_id, user_name):
    """Fetches one specific reading, used when opening the note editor.
    Checking user_name too prevents one user from editing another user's reading."""
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, category, card_name, meaning, orientation, group_id, note_text, note_image, note_image_position
        FROM readings
        WHERE id = ? AND user_name = ?
    """, (reading_id, user_name))
    row = cursor.fetchone()
    connection.close()
    return row


def save_note(reading_id, user_name, note_text, note_image, note_image_position):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE readings
        SET note_text = ?, note_image = ?, note_image_position = ?
        WHERE id = ? AND user_name = ?
    """, (note_text, note_image, note_image_position, reading_id, user_name))
    connection.commit()
    connection.close()


def get_oracle_groups(user_name):
    """Returns every past Oracle draw for this user as a grouped bundle:
    its past/present/future cards plus the AI story, all linked by group_id."""
    connection = create_connection()
    cursor = connection.cursor()

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

    connection.close()
    return groups


def limit_readings(user_name, category, max_rows):
    connection = create_connection()
    cursor = connection.cursor()
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
    connection.commit()
    connection.close()

