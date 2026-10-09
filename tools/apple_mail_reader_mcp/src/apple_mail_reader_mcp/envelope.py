"""Read-only queries against Mail.app Envelope Index (same idea as community mail-mcp)."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path


def locate_envelope_index() -> Path:
    mail_dir = Path.home() / "Library" / "Mail"
    if not mail_dir.is_dir():
        raise FileNotFoundError(f"Mail library not found: {mail_dir}")
    versions: list[tuple[int, str]] = []
    for entry in mail_dir.iterdir():
        m = re.fullmatch(r"V(\d+)", entry.name)
        if m and entry.is_dir():
            versions.append((int(m.group(1)), entry.name))
    if not versions:
        raise FileNotFoundError(f"No Mail/V* directory under {mail_dir}")
    versions.sort(reverse=True)
    db = mail_dir / versions[0][1] / "MailData" / "Envelope Index"
    if not db.is_file():
        raise FileNotFoundError(f"Envelope Index not found: {db}")
    return db


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


@dataclass
class SearchFilters:
    query: str | None = None
    from_substring: str | None = None
    subject_substring: str | None = None
    since: date | None = None
    unread_only: bool = False
    inbox_only: bool = True
    limit: int = 40


@dataclass
class MessageHit:
    rowid: int
    message_id: str | None
    subject: str
    from_address: str | None
    from_name: str | None
    date_received: str
    snippet: str | None
    read: bool
    flagged: bool
    mailbox_name: str | None
    mailbox_url: str

    def to_dict(self) -> dict:
        return {
            "rowid": self.rowid,
            "message_id": self.message_id,
            "subject": self.subject,
            "from_address": self.from_address,
            "from_name": self.from_name,
            "date_received": self.date_received,
            "snippet": self.snippet,
            "read": self.read,
            "flagged": self.flagged,
            "mailbox_name": self.mailbox_name,
            "mailbox_url": self.mailbox_url,
        }


def _parse_mailbox_name(url: str) -> str | None:
    try:
        from urllib.parse import unquote, urlparse

        parsed = urlparse(url)
        path = unquote(parsed.path.lstrip("/"))
        if path:
            return path
        return parsed.hostname or None
    except Exception:
        return None


def build_search_sql(filters: SearchFilters) -> str:
    where: list[str] = ["m.deleted = 0"]
    if filters.unread_only:
        where.append("m.read = 0")
    if filters.inbox_only:
        where.append("(mb.url LIKE '%INBOX%' OR mb.url LIKE '%收件箱%')")
    if filters.query:
        q = f"'%{_sql_escape(filters.query)}%'"
        where.append(
            f"(s.subject LIKE {q} OR a.address LIKE {q} OR a.comment LIKE {q} OR sm.summary LIKE {q})"
        )
    if filters.subject_substring:
        q = f"'%{_sql_escape(filters.subject_substring)}%'"
        where.append(f"s.subject LIKE {q}")
    if filters.from_substring:
        f = f"'%{_sql_escape(filters.from_substring)}%'"
        where.append(f"(a.address LIKE {f} OR a.comment LIKE {f})")
    if filters.since:
        since_ts = int(datetime.combine(filters.since, time.min).timestamp())
        where.append(f"m.date_received >= {since_ts}")

    limit = max(1, min(int(filters.limit), 200))
    where_clause = " AND ".join(where)
    return f"""
    SELECT
      m.ROWID AS rowid,
      mgd.message_id_header AS message_id_text,
      m.subject_prefix AS subject_prefix,
      s.subject AS subject_text,
      a.address AS sender_address,
      a.comment AS sender_comment,
      m.date_received AS date_received,
      sm.summary AS summary_text,
      m.read AS read,
      m.flagged AS flagged,
      mb.url AS mailbox_url
    FROM messages m
    LEFT JOIN subjects s ON s.ROWID = m.subject
    LEFT JOIN addresses a ON a.ROWID = m.sender
    LEFT JOIN summaries sm ON sm.ROWID = m.summary
    LEFT JOIN mailboxes mb ON mb.ROWID = m.mailbox
    LEFT JOIN message_global_data mgd ON mgd.ROWID = m.global_message_id
    WHERE {where_clause}
    ORDER BY m.date_received DESC
    LIMIT {limit};
    """


def query_envelope_json(db_path: Path, sql: str) -> list[dict]:
    """Read-only sqlite3 CLI (-readonly) to avoid writing WAL sidecars from Python open."""
    proc = subprocess.run(
        ["/usr/bin/sqlite3", "-readonly", "-json", str(db_path), sql],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(err or "sqlite3 query failed")
    raw = proc.stdout.strip()
    if not raw:
        return []
    return json.loads(raw)


def search_messages(filters: SearchFilters) -> list[MessageHit]:
    db = locate_envelope_index()
    sql = build_search_sql(filters)
    rows = query_envelope_json(db, sql)
    hits: list[MessageHit] = []
    for r in rows:
        subj = f"{r.get('subject_prefix') or ''}{r.get('subject_text') or ''}"
        ts = r.get("date_received")
        if ts:
            date_str = datetime.fromtimestamp(int(ts)).isoformat()
        else:
            date_str = ""
        snippet = r.get("summary_text")
        if snippet:
            snippet = re.sub(r"\s+", " ", snippet).strip()[:300]
        url = r.get("mailbox_url") or ""
        hits.append(
            MessageHit(
                rowid=int(r["rowid"]),
                message_id=r.get("message_id_text"),
                subject=subj,
                from_address=r.get("sender_address"),
                from_name=r.get("sender_comment") or None,
                date_received=date_str,
                snippet=snippet,
                read=bool(r.get("read")),
                flagged=bool(r.get("flagged")),
                mailbox_name=_parse_mailbox_name(url),
                mailbox_url=url,
            )
        )
    return hits


def envelope_available() -> tuple[bool, str]:
    try:
        locate_envelope_index()
        return True, "ok"
    except Exception as exc:
        return False, str(exc)
