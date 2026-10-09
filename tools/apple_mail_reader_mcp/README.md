# apple-mail-reader-mcp

## 背景

没有固定「刷邮箱」的习惯，但**支付、订阅、额度超限、安全验证**往往只发邮件；漏看会造成多扣费、服务中断或风险滞后。本 MCP 让 Agent 通过本机 **Mail.app + JXA** 做每日分拣：突出金钱与安全，其余营销/Digest 在你同意后再标已读或退订。

## 是什么

Local MCP server for **macOS Mail.app**: scan inbox, heuristic classification, mark read, unsubscribe.

读信路径：**JXA**（`osascript` → Mail.app）。在 **隐私与安全性 → 自动化** 中允许 IDE/终端控制「邮件」即可；Mail 可在后台运行，不必逐封打开窗口。

可选：`APPLE_MAIL_USE_ENVELOPE=1` 走本地 Envelope Index 加速（需完整磁盘访问，一般不必开）。

## Requirements

- macOS with **Mail.app** configured
- Python **3.11+**
- [uv](https://github.com/astral-sh/uv) recommended

## Install

```bash
cd tools/apple_mail_reader_mcp   # 若已克隆本仓库
uv sync
uv run apple-mail-reader-mcp   # stdio MCP  smoke test；Ctrl+C 退出
```

## Cursor `mcp.json`

```json
{
  "mcpServers": {
    "apple-mail-reader": {
      "command": "/absolute/path/to/tools/apple_mail_reader_mcp/.venv/bin/apple-mail-reader-mcp"
    }
  }
}
```

修改代码或配置后，在 Cursor 里 **重启 MCP**。

## Tools

| Tool | Purpose |
|------|---------|
| `security_info` | 能力说明与当前后端 |
| `scan_unread_or_today` | `mode`: `unread` \| `today` \| `unread_today` |
| `read_message` | 按 RFC `Message-ID` 读正文 |
| `get_unsubscribe_links` | 解析 List-Unsubscribe（不发 HTTP） |
| `mark_as_read` | 在 Mail.app 标已读 |
| `unsubscribe_message` | 预览或执行退订 |
| `triage_batch` | 批量标已读 + 退订（仅营销/订阅类） |

## Agent skill

[`.cursor/skills/apple-mail-reader/SKILL.md`](../../.cursor/skills/apple-mail-reader/SKILL.md) — 中文分拣话术与流程。

## Heuristic categories

`money`, `security`, `transactional`, `marketing`, `newsletter`, `other` — 见 `heuristics.py`，非 ML，金钱与安全请自行确认。

## License

MIT — [LICENSE](LICENSE)
