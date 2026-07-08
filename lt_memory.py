"""
credit: https://dev.to/satstack/give-your-ai-agent-long-term-memory-with-sqlite-and-ollama-4fon
with some minor adjustments
"""

import sqlite3
from datetime import datetime
import ollama
from pydantic.v1.config import get_config

from utilities import get_config

DB_PATH = get_config("DB_PATH","./lt_memory.db")

def init_db(db_path=DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            role            TEXT NOT NULL,
            tool_name       TEXT,
            tool_arguments  TEXT,
            content         TEXT NOT NULL,
            timestamp       TEXT NOT NULL,
            tokens_est      INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS summaries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            summary     TEXT NOT NULL,
            turn_range  TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS facts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT UNIQUE NOT NULL,
            value       TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_conv_session 
            ON conversations(session_id, timestamp);
    """)
    conn.commit()
    return conn

def save_turn(conn: sqlite3.Connection, session_id: str,
              role: str, content: str, tool_name: str='', tool_arguments: str=''):
    conn.execute(
        "INSERT INTO conversations (session_id, role, tool_name, tool_arguments, content, timestamp, tokens_est) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, role, tool_name, tool_arguments, content, datetime.utcnow().isoformat(),
         len(content.split()))
    )
    conn.commit()


def get_recent_turns(conn: sqlite3.Connection, session_id: str,
                     limit: int = 20) -> list[dict]:
    rows = conn.execute(
        "SELECT role, content, timestamp FROM conversations "
        "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    return [dict(r) for r in reversed(rows)]



def get_memory_context(conn: sqlite3.Connection,
                       current_session: str,
                       max_summaries: int = 3) -> str:
    sections = []
    facts = conn.execute(
        "SELECT key, value FROM facts ORDER BY updated_at DESC LIMIT 20"
    ).fetchall()

    if facts:
        facts_text = "\n".join(f"- {r['key']}: {r['value']}" for r in facts)
        sections.append(f"KNOWN FACTS ABOUT THE USER:\n{facts_text}")

    summaries = conn.execute(
        "SELECT session_id, summary, created_at FROM summaries "
        "WHERE session_id != ? ORDER BY created_at DESC LIMIT ?",
        (current_session, max_summaries)
    ).fetchall()

    if summaries:
        summary_text = "\n\n".join(
            f"[Session {r['session_id'][:8]}... on {r['created_at'][:10]}]\n{r['summary']}"
            for r in summaries
        )
        sections.append(f"PAST CONVERSATION SUMMARIES:\n{summary_text}")

    if not sections:
        return ""

    return "=== MEMORY ===\n" + "\n\n".join(sections) + "\n=== END MEMORY ===\n\n"


def upsert_fact(conn: sqlite3.Connection, key: str, value: str):
    conn.execute(
        "INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
        (key, value, datetime.utcnow().isoformat())
    )
    conn.commit()

def summarize_session(conn: sqlite3.Connection, session_id: str,
                      model: str|None) -> str | None:
    if model is None:
        model = get_config("MODEL", "gemma4")
    turns = conn.execute(
        "SELECT role, content FROM conversations "
        "WHERE session_id = ? ORDER BY id",
        (session_id,)
    ).fetchall()

    if len(turns) < 4:
        return None

    convo = "\n".join(f"{r['role'].upper()}: {r['content']}" for r in turns)

    prompt = f"""Summarize this conversation concisely. Focus on:
1. What the user was trying to accomplish
2. Key decisions or solutions reached
3. Any personal details mentioned (name, preferences, context)
4. Unresolved items or follow-ups needed

Keep it under 200 words.

CONVERSATION:
{convo}

SUMMARY:"""

    response = ollama.generate(model=model, prompt=prompt,
                               options={"temperature": 0.2})
    summary = response['response'].strip()

    turn_count = len(turns)
    conn.execute(
        "INSERT INTO summaries (session_id, summary, turn_range, created_at) "
        "VALUES (?, ?, ?, ?)",
        (session_id, summary, f"turns 1-{turn_count}",
         datetime.utcnow().isoformat())
    )
    conn.commit()

    print(f"[memory] Session {session_id[:8]} summarized ({turn_count} turns → {len(summary)} chars)")
    return summary

