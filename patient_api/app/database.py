import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "patients.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            VARCHAR(50)  NOT NULL,
            gender          VARCHAR(10)  NOT NULL,
            birth_date      DATE,
            phone           VARCHAR(20)  NOT NULL UNIQUE,
            id_card_masked  VARCHAR(18),
            id_card_last4   VARCHAR(4),
            id_card_hash    VARCHAR(64),
            address         VARCHAR(200),
            created_at      DATETIME     NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at      DATETIME     NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        """
    )
    conn.commit()
    conn.close()
