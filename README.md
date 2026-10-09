# apple-mail-reader-mcp

> **中文**：用本机 Mail.app + MCP，让 AI 帮你从邮件里揪出扣款、续费和安全告警，其余营销信再按需标已读或退订。  
> **English**: Local Mail.app MCP for AI triage—surface billing, renewals, and security alerts; mark noise read or unsubscribe only when you say so.

**隐私**：全程在本机 macOS 运行（Mail.app + JXA）；邮件内容只出现在你的 MCP 客户端对话里，**不上传邮箱到云端**。默认无网络；仅在你明确同意退订时，才会向发件人提供的退订链接发起 HTTP 请求。

## 为什么做

我平时**没有看邮件的习惯**，收件箱里大量是订阅和广告。但很多关键事只会发邮件：**支付扣款、订阅续费、额度/限额告警、登录验证**——漏看几天，可能多扣钱、服务被停，或账号风险发现太晚。

我不想为了偶尔扫一眼邮件，去配 IMAP 密码或把邮箱交给云端 Agent。macOS 自带 Mail.app 已经收着信，所以做了这个 MCP：**让任意支持 MCP 的本地 Agent**（例如 **Cursor、Codex、Hermes、OpenClaw** 等）通过本机 Mail + 自动化，每天帮我「分拣 + 提醒必看」；营销噪音在征得同意后再标已读或退订。

## 仓库结构

| 路径 | 说明 |
|------|------|
| [`tools/apple_mail_reader_mcp`](tools/apple_mail_reader_mcp/README.md) | MCP 安装、配置与工具说明 |
| [`.cursor/skills/apple-mail-reader`](.cursor/skills/apple-mail-reader/SKILL.md) | 分拣流程参考（中文；Cursor 可直接用，其他客户端可照流程提示词） |

## 快速开始

```bash
cd tools/apple_mail_reader_mcp
uv sync
```

在你的 **MCP 客户端**里把 server 指到 `.venv/bin/apple-mail-reader-mcp`（stdio）。在系统 **隐私与安全性 → 自动化** 里，允许**实际启动 osascript 的那个应用**（Cursor、终端、OpenClaw 等）控制「邮件」。配置示例见 [包内 README](tools/apple_mail_reader_mcp/README.md)。

## License

MIT — [LICENSE](tools/apple_mail_reader_mcp/LICENSE)
