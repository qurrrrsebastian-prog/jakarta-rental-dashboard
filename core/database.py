"""
SQLite database handler. Author: Avatar Putra Sigit.
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app.db")


def init_db() -> None:
    """Initialize SQLite database with tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            result_summary TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE,
            result_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dummy_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            value REAL,
            label TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_query(query: str, result_summary: str, session_id: str = "default") -> None:
    """Save query to history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO query_history (query, result_summary, session_id) VALUES (?, ?, ?)",
                  (query, result_summary, session_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error (save_query): {e}")


def get_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent query history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM query_history ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"DB Error (get_history): {e}")
        return []


def cache_result(cache_key: str, result: Dict[str, Any]) -> None:
    """Cache analysis result with an explicit local-time timestamp."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO analysis_cache (cache_key, result_json, timestamp) VALUES (?, ?, ?)",
            (cache_key, json.dumps(result), datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error (cache_result): {e}")


def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached result if exists (within 1 hour)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT result_json, timestamp FROM analysis_cache WHERE cache_key = ?", (cache_key,))
        row = c.fetchone()
        conn.close()
        if row:
            # Stored as local-time ISO (see cache_result); tolerate legacy 'Z' suffix.
            ts = datetime.fromisoformat(str(row[1]).replace("Z", "+00:00"))
            if ts.tzinfo is not None:
                ts = ts.replace(tzinfo=None)
            if (datetime.now() - ts).total_seconds() < 3600:
                return json.loads(row[0])
        return None
    except Exception:
        return None


def seed_dummy_data(category: str, values: List[Dict[str, Any]]) -> None:
    """Seed dummy data into database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for item in values:
            c.execute("INSERT INTO dummy_data (category, value, label) VALUES (?, ?, ?)",
                      (category, item.get("value"), item.get("label")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error (seed): {e}")


def get_dummy_data(category: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve dummy data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM dummy_data WHERE category = ? LIMIT ?", (category, limit))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []
