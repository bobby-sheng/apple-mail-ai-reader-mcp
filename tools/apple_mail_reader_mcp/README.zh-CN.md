# apple-mail-ai-reader-mcp（安装包）

[English](README.md) | **中文** · [项目总览](../../README.zh-CN.md)

**macOS Mail.app** 的 **MCP（stdio）** 服务：扫描、启发式分类、标已读、退订（需你确认）。适用于 **Cursor、Codex、Hermes、OpenClaw** 等任意 MCP 宿主。

读信：**JXA**（`osascript` → Mail.app）。在 **隐私与安全性 → 自动化** 中，允许启动 MCP 的宿主应用控制「邮件」。

可选：`APPLE_MAIL_USE_ENVELOPE=1` 使用 Envelope Index（需完整磁盘访问，一般不必）。

## 环境要求

- 仅 **macOS**
- 系统自带 **Mail.app** 且已登录邮箱
- Python **3.11+**
- 建议安装 [uv](https://github.com/astral-sh/uv)

## 安装

```bash
cd tools/apple_mail_reader_mcp
uv sync
uv run apple-mail-ai-reader-mcp   # 测试；Ctrl+C 退出
```

旧命令名 `apple-mail-reader-mcp` 仍可用（同一入口）。

## MCP 配置示例

```json
{
  "mcpServers": {
    "apple-mail-ai-reader": {
      "command": "/absolute/path/to/tools/apple_mail_reader_mcp/.venv/bin/apple-mail-ai-reader-mcp"
    }
  }
}
```

修改配置或代码后请 **重启 MCP**。

## 工具列表

| 工具 | 作用 |
|------|------|
| `security_info` | 能力说明 |
| `scan_unread_or_today` | `unread` / `today` / `unread_today` |
| `read_message` | 按 Message-ID 读正文 |
| `get_unsubscribe_links` | 解析退订链接 |
| `mark_as_read` | 标已读 |
| `unsubscribe_message` | 预览或执行退订 |
| `triage_batch` | 批量标已读与退订 |

## Agent 分拣流程

[`.cursor/skills/apple-mail-reader/SKILL.md`](../../.cursor/skills/apple-mail-reader/SKILL.md)

## 分类标签

`money`, `security`, `transactional`, `marketing`, `newsletter`, `other` — 见 `heuristics.py`。

## License

MIT — [LICENSE](LICENSE)
