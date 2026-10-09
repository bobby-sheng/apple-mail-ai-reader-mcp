# apple-mail-ai-reader-mcp

**English** | [中文](README.zh-CN.md)

<p align="center">
  <img src="docs/mail-app-icon.png" alt="macOS Mail.app" width="72" />
</p>

> Local **Mail.app** + **MCP** for **AI** triage: surface billing, renewals, and security alerts; mark marketing noise read or unsubscribe only when you say so.

**Platform:** **macOS only.** Uses Apple’s built-in **Mail.app** (accounts must be set up in Mail). This MCP reads and updates mail via **JXA**—not available on Windows or Linux.

**Privacy:** Runs entirely on your Mac (Mail.app + JXA). Message content stays local and appears only in your MCP client chat—**your inbox is not uploaded to a cloud agent**. No network by default; HTTP is used only when you explicitly approve an unsubscribe link.

## Why this exists

I don’t habitually check email—most of it is newsletters and ads. But **payments, subscription renewals, quota/limit warnings, and login verification** often arrive only by mail. Missing them for a few days can mean extra charges, service interruption, or late discovery of account risk.

I didn’t want to configure IMAP passwords or hand my mailbox to a remote agent. Mail.app already syncs on the Mac, so this MCP lets any **local MCP-capable agent** (**Cursor, Codex, Hermes, OpenClaw**, etc.) **triage daily** via Mail + Automation: highlight must-read money/security items; clean up noise only after you confirm.

## Repository layout

| Path | Description |
|------|-------------|
| [`tools/apple_mail_reader_mcp`](tools/apple_mail_reader_mcp/README.md) | Install, MCP config, tools |
| [`.cursor/skills/apple-mail-reader`](.cursor/skills/apple-mail-reader/SKILL.md) | Agent triage playbook (Chinese; reusable as prompts elsewhere) |

## Quick start

```bash
cd tools/apple_mail_reader_mcp
uv sync
```

Point your MCP client at `.venv/bin/apple-mail-ai-reader-mcp` (stdio). In **Privacy & Security → Automation**, allow the app that runs `osascript` (Cursor, Terminal, OpenClaw, etc.) to control **Mail**. Details: [package README](tools/apple_mail_reader_mcp/README.md).

## License

MIT — [LICENSE](tools/apple_mail_reader_mcp/LICENSE)
