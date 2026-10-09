# apple-mail-ai-reader-mcp (package)

**English** | [中文](README.zh-CN.md) · [Project overview](../../README.md)

Standard **MCP (stdio)** server for **macOS Mail.app**: scan, heuristic classification, mark read, unsubscribe (with your confirmation). Works with **Cursor, Codex, Hermes, OpenClaw**, or any MCP host.

Mail access: **JXA** (`osascript` → Mail.app). Grant **Automation** (control Mail) to the host app that launches this server.

Optional: `APPLE_MAIL_USE_ENVELOPE=1` for Envelope Index (Full Disk Access; usually unnecessary).

## Requirements

- **macOS** only
- **Mail.app** with at least one account
- Python **3.11+**
- [uv](https://github.com/astral-sh/uv) recommended

## Install

```bash
cd tools/apple_mail_reader_mcp
uv sync
uv run apple-mail-ai-reader-mcp   # smoke test; Ctrl+C to exit
```

Legacy CLI name `apple-mail-reader-mcp` still works (same entry point).

## MCP client config

```json
{
  "mcpServers": {
    "apple-mail-ai-reader": {
      "command": "/absolute/path/to/tools/apple_mail_reader_mcp/.venv/bin/apple-mail-ai-reader-mcp"
    }
  }
}
```

Restart the MCP server after config or code changes.

## Tools

| Tool | Purpose |
|------|---------|
| `security_info` | Capabilities and backend |
| `scan_unread_or_today` | `mode`: `unread` \| `today` \| `unread_today` |
| `read_message` | Body by RFC `Message-ID` |
| `get_unsubscribe_links` | Parse List-Unsubscribe (no HTTP) |
| `mark_as_read` | Mark read in Mail.app |
| `unsubscribe_message` | Plan or execute unsubscribe |
| `triage_batch` | Batch mark read + unsubscribe (marketing/newsletter) |

## Agent playbook

[`.cursor/skills/apple-mail-reader/SKILL.md`](../../.cursor/skills/apple-mail-reader/SKILL.md) — triage flow in Chinese.

## Heuristic categories

`money`, `security`, `transactional`, `marketing`, `newsletter`, `other` — see `heuristics.py`; not ML.

## License

MIT — [LICENSE](LICENSE)
