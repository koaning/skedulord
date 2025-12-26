import sqlite3
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
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_runs_name ON runs(name);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_start ON runs(start);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def insert_run(
    run_id: str,
    name: str,
    command: str,
    status: str,
    start: str,
    end: str,
    logpath: str,
) -> None:
    init_db()
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO runs (id, name, command, status, start, end, logpath)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, name, command, status, start, end, logpath),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_runs(
    limit: Optional[int] = None,
    name: Optional[str] = None,
    status: Optional[str] = None,
    date: Optional[str] = None,
) -> Iterable[sqlite3.Row]:
    init_db()
    conn = _connect()
    try:
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
        SELECT id, name, command, status, start, end, logpath
        FROM runs
        {where}
        ORDER BY start DESC
        {limit_clause}
        """
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def fetch_run(run_id: str) -> Optional[sqlite3.Row]:
    init_db()
    conn = _connect()
    try:
        return conn.execute(
            """
            SELECT id, name, command, status, start, end, logpath
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
    finally:
        conn.close()
