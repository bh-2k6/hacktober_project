import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from .config import DATABASE_PATH

Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_add_column(conn, table: str, column: str, column_def: str):
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                object_type TEXT,
                color TEXT,
                brand TEXT,
                characteristics TEXT DEFAULT '[]',
                distinctive_features TEXT DEFAULT '[]',
                visible_text TEXT,
                other_attributes TEXT DEFAULT '{}',
                location TEXT NOT NULL,
                date_time TEXT NOT NULL,
                image_path TEXT,
                image_phash TEXT,
                embedding TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'reunited', 'expired')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lost_item_id INTEGER NOT NULL,
                found_item_id INTEGER NOT NULL,
                score REAL NOT NULL,
                explanation TEXT NOT NULL,
                factor_scores TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'rejected')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lost_item_id) REFERENCES items(id) ON DELETE CASCADE,
                FOREIGN KEY (found_item_id) REFERENCES items(id) ON DELETE CASCADE,
                UNIQUE(lost_item_id, found_item_id)
            );

            CREATE TABLE IF NOT EXISTS contact_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                requester_type TEXT NOT NULL CHECK(requester_type IN ('lost_owner', 'found_finder')),
                message TEXT NOT NULL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
            CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
            CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
            CREATE INDEX IF NOT EXISTS idx_matches_lost ON matches(lost_item_id);
            CREATE INDEX IF NOT EXISTS idx_matches_found ON matches(found_item_id);
            CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
        """)

        _migrate_add_column(conn, "items", "embedding", "TEXT")


@contextmanager
def get_db_connection():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
