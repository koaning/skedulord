import sqlite3
from contextlib import contextmanager
from typing import Iterable, Optional

from skedulord.common import db_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    start TEXT NOT NULL,
    end TEXT NOT NULL,
    logpath TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_runs_name ON runs(name);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_start ON runs(start);
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _connection() -> Iterable[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connection() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def insert_run(
    run_id: str,
    name: str,
    command: str,
    status: str,
    start: str,
    end: str,
    logpath: str,
    attempt: int = 1,
) -> None:
    init_db()
    with _connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs (id, name, command, status, start, end, logpath, attempt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, name, command, status, start, end, logpath, attempt),
        )
        conn.commit()


def fetch_runs(
    limit: Optional[int] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    date: Optional[str] = None,
) -> Iterable[sqlite3.Row]:
    init_db()
    with _connection() as conn:
        clauses = []
        params = []
        if name:
            clauses.append("name LIKE ?")
            params.append(f"%{name}%")
        if status:
            clauses.append("status = ?")
            params.append(status)
        if date:
            clauses.append("start LIKE ?")
            params.append(f"%{date}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        limit_clause = f"LIMIT {int(limit)}" if limit else ""
        query = f"""
        SELECT id, name, command, status, start, end, logpath, attempt
        FROM runs
        {where}
        ORDER BY start DESC
        {limit_clause}
        """
        return conn.execute(query, params).fetchall()


def fetch_run(run_id: str) -> Optional[sqlite3.Row]:
    init_db()
    with _connection() as conn:
        return conn.execute(
            """
            SELECT id, name, command, status, start, end, logpath, attempt
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()


def fetch_user(username: str) -> Optional[sqlite3.Row]:
    init_db()
    with _connection() as conn:
        return conn.execute(
            """
            SELECT username, password_hash, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()


def insert_user(username: str, password_hash: str) -> bool:
    init_db()
    with _connection() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (username, password_hash),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_user_password(username: str, password_hash: str) -> bool:
    init_db()
    with _connection() as conn:
        cursor = conn.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE username = ?
            """,
            (password_hash, username),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_user(username: str) -> bool:
    init_db()
    with _connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM users
            WHERE username = ?
            """,
            (username,),
        )
        conn.commit()
        return cursor.rowcount > 0
