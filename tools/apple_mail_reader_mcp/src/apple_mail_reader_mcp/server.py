"""stdio MCP server — local Apple Mail triage (read + mark read + unsubscribe)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import use_envelope_index
from .envelope import SearchFilters, envelope_available, search_messages
from .heuristics import RiskCategory, classify_text
from .jxa import (
    extract_unsubscribe_urls,
    list_today_inbox_via_jxa,
    list_unread_via_jxa,
    mark_messages_read,
    message_source_headers,
    read_message_by_id,
)
from .unsubscribe import (
    build_unsubscribe_plan,
    execute_unsubscribe,
    is_safe_to_auto_unsubscribe,
)

mcp = FastMCP(
    "apple-mail-ai-reader",
    instructions=(
        "Local macOS Mail.app triage. Scan unread/today, classify money vs marketing. "
        "mark_as_read for noise; unsubscribe_message only for marketing/newsletter when execute=true. "
        "Never auto-mark or unsubscribe money/security categories."
    ),
)

PROTECTED_CATEGORIES = frozenset(
    {RiskCategory.MONEY.value, RiskCategory.SECURITY.value, RiskCategory.TRANSACTIONAL.value}
)

SECURITY_MANIFEST = {
    "network": "none by default; unsubscribe with execute=true sends HTTP POST/GET to List-Unsubscribe URLs only",
    "writes": "mark_as_read and unsubscribe (no send, trash, or move)",
    "data_stays_on_device": "except explicit unsubscribe HTTP to sender's unsubscribe endpoint",
    "email_content": "returned in tool responses to your MCP host (e.g. Cursor)",
    "full_disk_access": "not required — default path is Mail.app + JXA (Automation permission only)",
    "disk_access_envelope": "optional APPLE_MAIL_USE_ENVELOPE=1 for faster search (needs FDA)",
    "automation": "osascript controls Mail.app for lists, read status, bodies, unsubscribe headers",
    "logging": "does not write mail content to files",
    "source": "tools/apple_mail_reader_mcp/",
}


def _scan_via_jxa(mode: str, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if mode in ("today", "unread_today"):
        rows = list_today_inbox_via_jxa(limit=limit)
        for row in rows:
            if mode == "unread_today" and row.get("read"):
                continue
            subj = row.get("subject") or ""
            sender = row.get("sender") or ""
            clf = classify_text(subj, sender, None)
            items.append({**row, "heuristic": clf.to_dict(), "snippet": None})
    else:
        for row in list_unread_via_jxa(limit=limit):
            subj = row.get("subject") or ""
            sender = row.get("sender") or ""
            clf = classify_text(subj, sender, None)
            items.append({**row, "heuristic": clf.to_dict(), "snippet": None})
    return items


def _scan_via_envelope(
    mode: str, limit: int, inbox_only: bool, today: date
) -> list[dict[str, Any]]:
    unread_only = mode in ("unread", "unread_today")
    since = today if mode in ("today", "unread_today") else None
    hits = search_messages(
        SearchFilters(
            unread_only=unread_only,
            since=since,
            inbox_only=inbox_only,
            limit=limit,
        )
    )
    items: list[dict[str, Any]] = []
    for h in hits:
        sender = h.from_name or h.from_address or ""
        clf = classify_text(h.subject, sender, h.snippet)
        row = h.to_dict()
        row["heuristic"] = clf.to_dict()
        items.append(row)
    return items


@mcp.tool()
def security_info() -> str:
    """What this server does and does not do (for trust review)."""
    ok, detail = envelope_available()
    manifest = {
        **SECURITY_MANIFEST,
        "default_backend": "mail_app_jxa",
        "envelope_opt_in": use_envelope_index(),
        "envelope_index": {"available": ok, "detail": detail},
        "jxa_limits": "scans recent messages per inbox (see list_today_inbox_via_jxa per_mailbox_scan)",
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False)


@mcp.tool()
def scan_unread_or_today(
    mode: str = "unread",
    limit: int = 40,
    inbox_only: bool = True,
) -> str:
    """
    List messages for AI triage. mode: 'unread' | 'today' | 'unread_today'.
    Each item includes heuristic category — verify money items yourself.
    """
    mode = mode.strip().lower()
    if mode not in ("unread", "today", "unread_today"):
        raise ValueError("mode must be unread, today, or unread_today")

    today = date.today()
    items: list[dict[str, Any]] = []
    source = "mail_app_jxa"

    if use_envelope_index():
        try:
            items = _scan_via_envelope(mode, limit, inbox_only, today)
            source = "envelope_index"
        except Exception:
            items = _scan_via_jxa(mode, limit)
            source = "mail_app_jxa"
    else:
        items = _scan_via_jxa(mode, limit)

    money = [i for i in items if i.get("heuristic", {}).get("category") == "money"]
    summary = {
        "source": source,
        "mode": mode,
        "count": len(items),
        "money_alert_count": len(money),
        "messages": items,
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)


@mcp.tool()
def read_message(message_id: str, max_body_chars: int = 8000) -> str:
    """Read one message body by RFC Message-ID (from scan results)."""
    data = read_message_by_id(message_id, max_body_chars=max_body_chars)
    sender = str(data.get("from") or "")
    subj = str(data.get("subject") or "")
    body = str(data.get("body") or "")
    clf = classify_text(subj, sender, body[:500])
    data["heuristic"] = clf.to_dict()
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
def get_unsubscribe_links(message_id: str) -> str:
    """Extract List-Unsubscribe header URLs and body unsubscribe links (no HTTP)."""
    raw = message_source_headers(message_id)
    urls = extract_unsubscribe_urls(raw)
    split_idx = raw.find("|||SPLIT|||")
    headers = raw[:split_idx] if split_idx >= 0 else raw
    plan = build_unsubscribe_plan(
        message_id,
        urls.get("header", []),
        urls.get("body", []),
        headers,
    )
    return json.dumps(plan.to_dict(), indent=2, ensure_ascii=False)


@mcp.tool()
def mark_as_read(message_ids: list[str]) -> str:
    """
    Mark messages as read in Mail.app by RFC Message-ID.
    Use for marketing/newsletter noise after you (or AI) reviewed — avoid money/security mail.
    """
    if not message_ids:
        raise ValueError("message_ids must be a non-empty list")
    result = mark_messages_read(message_ids)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
def unsubscribe_message(
    message_id: str,
    execute: bool = False,
    category_hint: str = "",
) -> str:
    """
    Plan or execute unsubscribe for one message.
    execute=false: plan only. execute=true: HTTP one-click/GET or open mailto (network only then).
    Refuses if category_hint is money, security, or transactional.
    """
    hint = category_hint.strip().lower()
    if hint in PROTECTED_CATEGORIES:
        return json.dumps(
            {
                "ok": False,
                "skipped": True,
                "reason": f"protected category: {hint}",
            },
            indent=2,
        )

    raw = message_source_headers(message_id)
    split_idx = raw.find("|||SPLIT|||")
    headers = raw[:split_idx] if split_idx >= 0 else raw
    urls = extract_unsubscribe_urls(raw)
    plan = build_unsubscribe_plan(
        message_id,
        urls.get("header", []),
        urls.get("body", []),
        headers,
    )
    out: dict[str, Any] = {"plan": plan.to_dict(), "executed": False}
    if not execute:
        out["hint"] = "Set execute=true to perform unsubscribe after you approve."
        return json.dumps(out, indent=2, ensure_ascii=False)

    if hint and not is_safe_to_auto_unsubscribe(hint):
        out["ok"] = False
        out["reason"] = "category_hint not in marketing/newsletter; refusing execute"
        return json.dumps(out, indent=2)

    result = execute_unsubscribe(plan)
    out["executed"] = True
    out["result"] = result
    return json.dumps(out, indent=2, ensure_ascii=False)


@mcp.tool()
def triage_batch(
    mark_read_message_ids: list[str] | None = None,
    unsubscribe_items: list[dict[str, str]] | None = None,
) -> str:
    """
    Batch after scan: mark read + optional unsubscribe.
    unsubscribe_items: [{"message_id": "...", "category": "marketing"}, ...]
    Skips unsubscribe for non marketing/newsletter categories. Always skips money/security/transactional for mark_read if category provided in parallel scan — pass only safe IDs.
    """
    mark_read_message_ids = mark_read_message_ids or []
    unsubscribe_items = unsubscribe_items or []

    mark_result: dict[str, Any] | None = None
    if mark_read_message_ids:
        mark_result = mark_messages_read(mark_read_message_ids)

    unsub_results: list[dict[str, Any]] = []
    for item in unsubscribe_items[:20]:
        mid = (item.get("message_id") or "").strip()
        cat = (item.get("category") or "").strip().lower()
        if not mid:
            continue
        if cat in PROTECTED_CATEGORIES:
            unsub_results.append({"message_id": mid, "skipped": True, "reason": "protected"})
            continue
        if cat and not is_safe_to_auto_unsubscribe(cat):
            unsub_results.append({"message_id": mid, "skipped": True, "reason": "not marketing/newsletter"})
            continue
        raw = message_source_headers(mid)
        split_idx = raw.find("|||SPLIT|||")
        headers = raw[:split_idx] if split_idx >= 0 else raw
        urls = extract_unsubscribe_urls(raw)
        plan = build_unsubscribe_plan(mid, urls.get("header", []), urls.get("body", []), headers)
        exec_result = execute_unsubscribe(plan)
        unsub_results.append({"message_id": mid, "plan": plan.to_dict(), "result": exec_result})
        if exec_result.get("ok"):
            mark_messages_read([mid])

    return json.dumps(
        {"mark_read": mark_result, "unsubscribe": unsub_results},
        indent=2,
        ensure_ascii=False,
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
