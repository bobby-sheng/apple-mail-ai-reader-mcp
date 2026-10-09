---
name: apple-mail-reader
description: >-
  通过 macOS Mail.app + JXA 的本地 MCP 做收件箱分拣：扫描今日/未读、金钱与安全必看、营销与 Digest 经用户确认后标已读或退订。
  用于「今天邮件」「收件箱」「Mail.app」「标已读」「退订」、apple-mail-reader MCP。
---

# Apple Mail 本地分拣（MCP）

**读信方式**：`osascript`（JXA）控制本机 **Mail.app**，经脚本接口取主题、发件人、正文等。需在系统 **隐私与安全性 → 自动化** 中，允许当前宿主（如 Cursor）控制「邮件」。Mail 可在后台运行，不必把每封信在窗口里打开。

**MCP 命名空间**：`user-apple-mail-reader`（以实际配置的 server 名为准）。

## 扫描

1. 今日：`scan_unread_or_today(mode="today", limit=80)`。
2. 未读：`mode="unread"` 或 `mode="unread_today"`。
3. 扫不到信时：确认 Mail.app 已登录、自动化权限已开，并 **重启 MCP** 后再试。

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

## JXA 与 Mail.app（用户问起时）

脚本通过 Apple Events 问 Mail：某账号收件箱里最近若干封里，哪些符合「今日 / 未读」等条件。数据来自 Mail 已同步到本机的邮件，不是 IDE 自己去扫邮件库目录。

**限制**：每个收件箱只遍历最近一段邮件再按日期过滤，排序很靠后或很深的「今日」信有可能漏掉。

## 安装

见仓库 `tools/apple_mail_reader_mcp/README.md`。
