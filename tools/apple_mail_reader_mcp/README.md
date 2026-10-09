# apple-mail-reader-mcp

Local [MCP](https://modelcontextprotocol.io/) server for **macOS Mail.app**: scan inbox, classify heuristically, mark read, and unsubscribe — without giving your IDE Full Disk Access.

Default path: **JXA** (`osascript` → Mail.app). Optional fast path: SQLite Envelope Index (`APPLE_MAIL_USE_ENVELOPE=1`, requires FDA).

## Requirements

- macOS with **Mail.app** configured
- Python **3.11+**
- [uv](https://github.com/astral-sh/uv) recommended

## Permissions

| Mode | What to grant |
|------|----------------|
| **Default (JXA)** | **Privacy & Security → Automation**: allow **Cursor** (or your terminal) to control **Mail** |
| Optional envelope index | **Full Disk Access** for the process reading `~/Library/Mail` — only if `APPLE_MAIL_USE_ENVELOPE=1` |

Mail may launch in the background; no need to open each message in the UI.

## Install

```bash
cd tools/apple_mail_reader_mcp
uv sync
uv run apple-mail-reader-mcp   # smoke test (stdio MCP; Ctrl+C to exit)
```

## Cursor `mcp.json`

```json
{
  "mcpServers": {
    "apple-mail-reader": {
      "command": "/absolute/path/to/tools/apple_mail_reader_mcp/.venv/bin/apple-mail-reader-mcp",
      "env": {
        "APPLE_MAIL_USE_ENVELOPE": "0"
      }
    }
  }
}
```

Restart the MCP server in Cursor after code or config changes.

## Tools

| Tool | Purpose |
|------|---------|
| `security_info` | Trust manifest + backend (`mail_app_jxa` vs envelope) |
| `scan_unread_or_today` | `mode`: `unread` \| `today` \| `unread_today` |
| `read_message` | Body by RFC `Message-ID` |
| `get_unsubscribe_links` | Parse List-Unsubscribe (no network) |
| `mark_as_read` | Set read in Mail.app |
| `unsubscribe_message` | Plan (`execute=false`) or HTTP/mailto unsubscribe (`execute=true`) |
| `triage_batch` | Batch mark read + unsubscribe (marketing/newsletter only) |

## Agent skill

Project skill for Cursor agents: [`.cursor/skills/apple-mail-reader/SKILL.md`](../../.cursor/skills/apple-mail-reader/SKILL.md) — daily triage workflow in Chinese.

## Heuristic categories

`money`, `security`, `transactional`, `marketing`, `newsletter`, `other` — keyword/sender rules in `heuristics.py`. Not ML; verify money and security yourself.

## License

MIT — see [LICENSE](LICENSE).
