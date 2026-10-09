"""One-click unsubscribe via List-Unsubscribe headers (optional outbound HTTP)."""

from __future__ import annotations

import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


@dataclass
class UnsubscribePlan:
    message_id: str
    header_urls: list[str]
    body_urls: list[str]
    one_click_post_url: str | None
    mailto_urls: list[str]
    recommended: Literal["one_click_post", "https_get", "mailto", "manual"] | None  # noqa: UP007
    note: str

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "header_urls": self.header_urls,
            "body_urls": self.body_urls,
            "one_click_post_url": self.one_click_post_url,
            "mailto_urls": self.mailto_urls,
            "recommended": self.recommended,
            "note": self.note,
        }


def _parse_list_unsubscribe_post(headers: str) -> str | None:
    m = re.search(r"^List-Unsubscribe-Post:\s*(.+)$", headers, re.I | re.M)
    if not m:
        return None
    if "one-click" not in (m.group(1) or "").lower():
        return None
    m2 = re.search(
        r"^List-Unsubscribe:[ \t]*((?:[^\r\n]|\r?\n[ \t])*)",
        headers,
        re.I | re.M,
    )
    if not m2:
        return None
    value = re.sub(r"\r?\n[ \t]+", " ", m2.group(1) or "")
    for match in re.finditer(r"<(https?://[^>]+)>", value, re.I):
        return match.group(1)
    return None


def build_unsubscribe_plan(
    message_id: str,
    header_urls: list[str],
    body_urls: list[str],
    raw_headers: str,
) -> UnsubscribePlan:
    mailto = [u for u in header_urls if u.lower().startswith("mailto:")]
    https_header = [u for u in header_urls if u.lower().startswith("http")]
    post_url = _parse_list_unsubscribe_post(raw_headers)

    recommended: Literal["one_click_post", "https_get", "mailto", "manual"] | None = None
    note = ""
    if post_url:
        recommended = "one_click_post"
        note = "RFC 8058 one-click POST (preferred when present)."
    elif https_header:
        recommended = "https_get"
        note = "Will request first https List-Unsubscribe URL (may require cookies in browser)."
    elif mailto:
        recommended = "mailto"
        note = "Opens Mail compose to unsubscribe address via macOS open."
    elif body_urls:
        recommended = "https_get"
        note = "Uses body unsubscribe link (less reliable)."
    else:
        recommended = None
        note = "No automatic path; manual unsubscribe only."

    return UnsubscribePlan(
        message_id=message_id,
        header_urls=header_urls,
        body_urls=body_urls,
        one_click_post_url=post_url,
        mailto_urls=mailto,
        recommended=recommended,
        note=note,
    )


def execute_unsubscribe(plan: UnsubscribePlan, timeout: float = 20.0) -> dict:
    """Perform unsubscribe. Uses network only for http(s) one-click / GET."""
    if plan.recommended is None:
        return {"ok": False, "action": "none", "detail": plan.note}

    if plan.recommended == "one_click_post" and plan.one_click_post_url:
        url = plan.one_click_post_url
        req = urllib.request.Request(
            url,
            data=b"List-Unsubscribe=One-Click",
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Apple-Mail-Reader-MCP/0.2 (one-click unsubscribe)",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
                code = resp.getcode()
            return {"ok": 200 <= code < 400, "action": "one_click_post", "url": url, "status": code}
        except urllib.error.HTTPError as exc:
            return {
                "ok": False,
                "action": "one_click_post",
                "url": url,
                "status": exc.code,
                "detail": str(exc.reason),
            }
        except Exception as exc:
            return {"ok": False, "action": "one_click_post", "url": url, "detail": str(exc)}

    if plan.recommended == "https_get":
        url = next(
            (u for u in plan.header_urls if u.lower().startswith("http")),
            plan.body_urls[0] if plan.body_urls else None,
        )
        if not url:
            return {"ok": False, "action": "https_get", "detail": "no https url"}
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "Apple-Mail-Reader-MCP/0.2 (unsubscribe)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
                code = resp.getcode()
            return {"ok": 200 <= code < 400, "action": "https_get", "url": url, "status": code}
        except urllib.error.HTTPError as exc:
            return {
                "ok": exc.code in (301, 302, 303, 307, 308),
                "action": "https_get",
                "url": url,
                "status": exc.code,
                "detail": str(exc.reason),
            }
        except Exception as exc:
            return {"ok": False, "action": "https_get", "url": url, "detail": str(exc)}

    if plan.recommended == "mailto" and plan.mailto_urls:
        import subprocess

        url = plan.mailto_urls[0]
        subprocess.run(["/usr/bin/open", url], check=False)
        return {"ok": True, "action": "mailto_open", "url": url, "detail": "Opened mailto in Mail."}

    return {"ok": False, "action": "unknown", "detail": plan.note}


def is_safe_to_auto_unsubscribe(category: str) -> bool:
    return category in ("marketing", "newsletter")
