"""Mail.app access via osascript (Automation permission). Read-only operations."""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any


def run_jxa(script: str, timeout: float = 45.0) -> str:
    proc = subprocess.run(
        ["/usr/bin/osascript", "-l", "JavaScript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "osascript failed").strip()
        raise RuntimeError(err)
    return proc.stdout.strip()


def _escape_js_string(value: str) -> str:
    return json.dumps(value)


def list_today_inbox_via_jxa(limit: int = 80, per_mailbox_scan: int = 150) -> list[dict[str, Any]]:
    script = f"""
function run() {{
  const limit = {max(1, min(limit, 120))};
  const scan = {max(50, min(per_mailbox_scan, 300))};
  const Mail = Application("Mail");
  const out = [];
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const accounts = Mail.accounts();
  for (let i = 0; i < accounts.length; i++) {{
    const acct = accounts[i];
    const acctName = acct.name();
    const mailboxes = acct.mailboxes();
    for (let j = 0; j < mailboxes.length; j++) {{
      const mb = mailboxes[j];
      const mbName = mb.name();
      if (mbName !== "INBOX" && mbName !== "收件箱" && mbName !== "Inbox") continue;
      const msgs = mb.messages();
      const n = Math.min(msgs.length, scan);
      for (let k = 0; k < n && out.length < limit; k++) {{
        const msg = msgs[k];
        const dr = msg.dateReceived();
        if (dr < start) continue;
        out.push({{
          account: acctName,
          mailbox: mbName,
          message_id: msg.messageId(),
          subject: msg.subject(),
          sender: String(msg.sender()),
          date_received: dr.toISOString(),
          read: msg.readStatus(),
        }});
      }}
    }}
  }}
  return JSON.stringify(out);
}}
"""
    raw = run_jxa(script, timeout=180.0)
    return json.loads(raw or "[]")


def list_unread_via_jxa(limit: int = 30) -> list[dict[str, Any]]:
    script = f"""
function run() {{
  const limit = {max(1, min(limit, 80))};
  const Mail = Application("Mail");
  const out = [];
  const accounts = Mail.accounts();
  for (let i = 0; i < accounts.length; i++) {{
    const acct = accounts[i];
    const acctName = acct.name();
    const mailboxes = acct.mailboxes();
    for (let j = 0; j < mailboxes.length; j++) {{
      const mb = mailboxes[j];
      const mbName = mb.name();
      if (mbName !== "INBOX" && mbName !== "收件箱" && mbName !== "Inbox") continue;
      const msgs = mb.messages();
      const n = Math.min(msgs.length, 200);
      for (let k = 0; k < n && out.length < limit; k++) {{
        const msg = msgs[k];
        if (msg.readStatus()) continue;
        out.push({{
          account: acctName,
          mailbox: mbName,
          message_id: msg.messageId(),
          subject: msg.subject(),
          sender: String(msg.sender()),
          date_received: msg.dateReceived().toISOString(),
        }});
      }}
      if (out.length >= limit) break;
    }}
    if (out.length >= limit) break;
  }}
  return JSON.stringify(out);
}}
"""
    raw = run_jxa(script, timeout=120.0)
    return json.loads(raw or "[]")


def read_message_by_id(message_id: str, max_body_chars: int = 8000) -> dict[str, Any]:
    bare = message_id.strip().lstrip("<").rstrip(">")
    mid = _escape_js_string(bare)
    max_chars = max(500, min(max_body_chars, 20000))
    script = f"""
function run() {{
  const targetId = {mid};
  const Mail = Application("Mail");
  const accounts = Mail.accounts();
  for (let i = 0; i < accounts.length; i++) {{
    const mailboxes = accounts[i].mailboxes();
    for (let j = 0; j < mailboxes.length; j++) {{
      const mb = mailboxes[j];
      const msgs = mb.messages.whose({{ messageId: targetId }});
      if (msgs.length === 0) continue;
      const msg = msgs[0];
      let body = String(msg.content());
      if (body.length > {max_chars}) body = body.slice(0, {max_chars});
      return JSON.stringify({{
        subject: msg.subject(),
        from: String(msg.sender()),
        date_received: msg.dateReceived().toISOString(),
        read: msg.readStatus(),
        flagged: msg.flaggedStatus(),
        body: body,
        message_id: msg.messageId(),
      }});
    }}
  }}
  return "NOTFOUND";
}}
"""
    raw = run_jxa(script, timeout=60.0)
    if raw == "NOTFOUND":
        raise LookupError(f"No message with id {message_id}")
    return json.loads(raw)


def message_source_headers(message_id: str, header_bytes: int = 8000) -> str:
    bare = message_id.strip().lstrip("<").rstrip(">")
    mid = _escape_js_string(bare)
    script = f"""
function run() {{
  const targetId = {mid};
  const Mail = Application("Mail");
  const accounts = Mail.accounts();
  for (let i = 0; i < accounts.length; i++) {{
    const mailboxes = accounts[i].mailboxes();
    for (let j = 0; j < mailboxes.length; j++) {{
      const msgs = mailboxes[j].messages.whose({{ messageId: targetId }});
      if (msgs.length === 0) continue;
      let src = String(msgs[0].source());
      if (src.length > {header_bytes}) src = src.slice(0, {header_bytes});
      const body = String(msgs[0].content());
      return src + "|||SPLIT|||" + body;
    }}
  }}
  return "NOTFOUND";
}}
"""
    raw = run_jxa(script, timeout=60.0)
    if raw == "NOTFOUND":
        raise LookupError(f"No message with id {message_id}")
    return raw


SPLIT = "|||SPLIT|||"


def mark_messages_read(message_ids: list[str], timeout: float = 120.0) -> dict[str, Any]:
    """Set read status on messages by RFC Message-ID. Mutates Mail.app only."""
    ids = [m.strip().lstrip("<").rstrip(">") for m in message_ids if m and m.strip()]
    ids = ids[:50]
    if not ids:
        return {"marked": 0, "not_found": [], "errors": []}
    ids_json = json.dumps(ids)
    script = f"""
function run() {{
  const ids = {ids_json};
  const Mail = Application("Mail");
  const notFound = [];
  let marked = 0;
  for (let t = 0; t < ids.length; t++) {{
    const targetId = ids[t];
    let hit = false;
    const accounts = Mail.accounts();
    for (let i = 0; i < accounts.length; i++) {{
      const mailboxes = accounts[i].mailboxes();
      for (let j = 0; j < mailboxes.length; j++) {{
        const msgs = mailboxes[j].messages.whose({{ messageId: targetId }});
        if (msgs.length === 0) continue;
        const msg = msgs[0];
        msg.readStatus = true;
        marked++;
        hit = true;
        break;
      }}
      if (hit) break;
    }}
    if (!hit) notFound.push(targetId);
  }}
  return JSON.stringify({{ marked: marked, not_found: notFound }});
}}
"""
    raw = run_jxa(script, timeout=timeout)
    return json.loads(raw or '{"marked":0,"not_found":[]}')


def extract_unsubscribe_urls(raw: str) -> dict[str, list[str]]:
    split_idx = raw.find(SPLIT)
    headers = raw[:split_idx] if split_idx >= 0 else raw
    body = raw[split_idx + len(SPLIT) :] if split_idx >= 0 else ""

    header_urls: list[str] = []
    body_urls: list[str] = []

    match = re.search(
        r"^List-Unsubscribe:[ \t]*((?:[^\r\n]|\r?\n[ \t])*)",
        headers,
        re.IGNORECASE | re.MULTILINE,
    )
    if match:
        value = re.sub(r"\r?\n[ \t]+", " ", match.group(1) or "")
        for m in re.finditer(r"<([^>]+)>", value):
            header_urls.append(m.group(1))

    url_re = re.compile(r'https?://[^\s<>"\')\]]+')
    for m in url_re.finditer(body):
        url = m.group(0).rstrip(".,;")
        if re.search(r"unsubscribe|opt.?out|optout|remove", url, re.I):
            if url not in header_urls and url not in body_urls:
                body_urls.append(url)

    return {"header": header_urls, "body": body_urls}
