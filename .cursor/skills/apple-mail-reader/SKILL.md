---
name: apple-mail-reader
description: >-
  通过 macOS Mail.app + JXA 的本地 MCP 做收件箱分拣：扫描今日/未读、金钱与安全必看、营销与 Digest 经用户确认后标已读或退订。
  用于「今天邮件」「收件箱」「Mail.app」「标已读」「退订」、apple-mail-reader MCP，或用户要求不用完整磁盘访问、只走自动化读邮件时。
---

# Apple Mail 本地分拣（MCP）

**原则**：默认 **Mail.app + JXA**（系统「自动化」权限），**不要**要求用户给 Cursor 完整磁盘访问。仅当用户明确要更快全库检索时，才提及可选环境变量 `APPLE_MAIL_USE_ENVELOPE=1`（需 FDA）。

**MCP 命名空间**：`user-apple-mail-reader`（以 Cursor 里配置的 server 名为准）。

## 扫描

1. 先可选调用 `security_info`，确认 `default_backend` 为 `mail_app_jxa`、`envelope_opt_in` 为 false。
2. 用户要看今日：`scan_unread_or_today(mode="today", limit=80)`。
3. 只看未读：`mode="unread"` 或 `mode="unread_today"`。
4. 若 `source` 不是 `mail_app_jxa` 或 today 报 Envelope 错误：提示用户在 Cursor **重启 MCP**，并确认 `mcp.json` 中 `APPLE_MAIL_USE_ENVELOPE=0`（或未设置）。

## 分类与呈现（中文）

对 `messages[]` 中每条的 `heuristic.category` 归类展示，**覆盖误判**（例如主题含「验证」「登录」但发件人是 noreply → 仍按安全说明）。

| 区块 | 类别 | 说明 |
|------|------|------|
| **必看 · 金钱/账单** | `money` | 发票、扣款、订单、续费等 |
| **必看 · 安全/验证码** | `security` | 验证码、异常登录、verify login |
| **建议扫一眼** | `transactional`、`other`（重要通知） | 用**中文**解释这封是促销、资讯周刊、购物提醒还是条款更新，并写「一般需要做什么」 |
| **Digest / Newsletter** | `newsletter` | 摘要订阅 |
| **营销噪音** | `marketing` | 推销、研讨会邀请等 |

启发式仅供参考；金钱类务必让人工确认。

## 写操作（必须经用户确认）

- **标已读**：`mark_as_read(message_ids)` — 仅对用户点名的 ID；**禁止**对 `money` / `security` / `transactional` 批量误标（用户明确包含时除外）。
- **退订**：先 `get_unsubscribe_links` 或 `unsubscribe_message(execute=false)` 展示计划；用户同意后再 `execute=true` 或 `triage_batch`。`category_hint` 为 money/security/transactional 时**拒绝执行**。
- 营销/Digest：列出编号，问用户「标已读 / 退订 / 跳过」。

## JXA 原理（用户问起时简要说明）

`osascript` 通过 Apple Events 调用 Mail 脚本接口读 `subject` / `sender` / `content`，**不**直接读 `~/Library/Mail` 文件。Mail 可在后台被拉起，**不必**前台打开每一封信。

限制：每个收件箱只扫最近若干封再按日期过滤，极深处或排序靠后的「今日」信可能漏扫。

## 安装与配置

见仓库 `tools/apple_mail_reader_mcp/README.md`。
