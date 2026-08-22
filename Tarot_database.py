import sqlite3


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
    connection.commit()
    connection.close()


def save_reading(user_name, category, card_name, meaning, orientation):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO readings (user_name, category, card_name, meaning, orientation)
        VALUES (?, ?, ?, ?, ?)
    """, (user_name, category, card_name, meaning, orientation))
    connection.commit()
    connection.close()


def get_readings(user_name, category):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT card_name, meaning, orientation FROM readings
        WHERE user_name = ? AND category = ?
    """, (user_name, category))
    rows = cursor.fetchall()
    connection.close()
    return rows


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

