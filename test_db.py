"""
test_db.py

Quick script to check that your app can connect to the Supabase (PostgreSQL)
database using the DATABASE_URL from your .env file.

Run it from your project's root folder with:
    python test_db.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load variables from .env (DATABASE_URL, etc.)
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL is not set. Check your .env file.")
    exit(1)

print("Trying to connect to the database...")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.fetchone()
        print(f"✅ Connection successful! Test query returned: {value}")

        # Bonus: list existing tables so you can confirm your schema is there
        tables = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        table_names = [row[0] for row in tables]
        if table_names:
            print(f"📋 Tables found in your database: {', '.join(table_names)}")
        else:
            print("📋 No tables found yet — you still need to run your CREATE TABLE statements.")

except Exception as e:
    print("❌ Connection failed.")
    print(f"Error: {e}")