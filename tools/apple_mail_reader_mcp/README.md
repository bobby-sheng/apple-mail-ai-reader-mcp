# apple-mail-reader-mcp

## 背景

没有固定「刷邮箱」的习惯，但**支付、订阅、额度超限、安全验证**往往只发邮件；漏看会造成多扣费、服务中断或风险滞后。本 MCP 让 Agent 通过本机 **Mail.app + JXA** 做每日分拣：突出金钱与安全，其余营销/Digest 在你同意后再标已读或退订。

## 是什么

**标准 MCP（stdio）** 服务，不绑定某一 IDE。凡能挂载 MCP server 的环境都可以用，例如 **Cursor、Codex、Hermes、OpenClaw** 等——由客户端把工具暴露给背后的模型即可。

能力：扫描收件箱、启发式分类、标已读、退订（需你确认）。

读信路径：**JXA**（`osascript` → Mail.app）。在 **隐私与安全性 → 自动化** 中，允许**启动该 MCP 的宿主应用**控制「邮件」；Mail 可在后台运行，不必逐封打开窗口。

可选：`APPLE_MAIL_USE_ENVELOPE=1` 走本地 Envelope Index 加速（需完整磁盘访问，一般不必开）。

## Requirements

- macOS with **Mail.app** configured
- Python **3.11+**
- [uv](https://github.com/astral-sh/uv) recommended
- 任意支持 MCP 的客户端

## Install

```bash
cd tools/apple_mail_reader_mcp   # 克隆本仓库后
uv sync
uv run apple-mail-reader-mcp   # stdio MCP smoke test；Ctrl+C 退出
```

## MCP 客户端配置

本质是：用 **command** 启动 `apple-mail-reader-mcp`，传输为 **stdio**。各产品配置文件名不同，字段含义相同。

**Cursor**（`mcp.json`）示例：

```json
{
  "mcpServers": {
    "apple-mail-reader": {
      "command": "/absolute/path/to/tools/apple_mail_reader_mcp/.venv/bin/apple-mail-reader-mcp"
    }
  }
}
```

**Codex / Hermes / OpenClaw** 等：在各自的 MCP 设置里填写同样的 `command`（或 `uv run --directory … apple-mail-reader-mcp`），保存后**重启 MCP 或客户端**。

自动化权限授予给**真正跑 osascript 的进程所属 App**（不一定是 Python 本身）。

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

## Agent 分拣流程（可选）

[`.cursor/skills/apple-mail-reader/SKILL.md`](../../.cursor/skills/apple-mail-reader/SKILL.md) — 中文话术：今日邮件怎么分类、何时标已读/退订。非 Cursor 用户可把该文件内容当作 system / 技能提示给模型。

## Heuristic categories

`money`, `security`, `transactional`, `marketing`, `newsletter`, `other` — 见 `heuristics.py`，非 ML，金钱与安全请自行确认。

## License

MIT — [LICENSE](LICENSE)
