# apple-mail-reader-mcp

本地 macOS **Mail.app** 的 [MCP](https://modelcontextprotocol.io/) 服务：用 **JXA** 扫今日/未读邮件，粗分账单与安全类「必看」，营销与 Digest 经你确认后再标已读或退订。

## 为什么做

我平时**没有看邮件的习惯**，收件箱里大量是订阅和广告。但很多关键事只会发邮件：**支付扣款、订阅续费、额度/限额告警、登录验证**——漏看几天，可能多扣钱、服务被停，或账号风险发现太晚。

我不想为了偶尔扫一眼邮件，去配 IMAP 密码或把邮箱交给云端 Agent。macOS 自带 Mail.app 已经收着信，所以做了这个 MCP：**让 Cursor 里的 AI 通过本机 Mail + 自动化，每天帮我「分拣 + 提醒必看」**，噪音在征得同意后再标已读或退订。

## 仓库结构

| 路径 | 说明 |
|------|------|
| [`tools/apple_mail_reader_mcp`](tools/apple_mail_reader_mcp/README.md) | MCP 安装、配置与工具说明 |
| [`.cursor/skills/apple-mail-reader`](.cursor/skills/apple-mail-reader/SKILL.md) | Agent 分拣流程（中文） |

## 快速开始

```bash
cd tools/apple_mail_reader_mcp
uv sync
```

在 Cursor 的 `mcp.json` 里指向 `.venv/bin/apple-mail-reader-mcp`，并在系统 **自动化** 里允许 Cursor 控制「邮件」。细节见 [包内 README](tools/apple_mail_reader_mcp/README.md)。

## License

MIT — [LICENSE](tools/apple_mail_reader_mcp/LICENSE)
