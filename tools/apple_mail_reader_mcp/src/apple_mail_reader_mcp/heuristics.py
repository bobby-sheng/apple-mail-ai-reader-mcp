"""Local keyword heuristics for money / marketing (no network, no ML)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class RiskCategory(str, Enum):
    MONEY = "money"
    SECURITY = "security"
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    NEWSLETTER = "newsletter"
    OTHER = "other"


@dataclass
class Classification:
    category: RiskCategory
    priority: int  # 0 = highest
    reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "priority": self.priority,
            "reasons": self.reasons,
        }


MONEY_PATTERNS = [
    r"\breceipt\b",
    r"\binvoice\b",
    r"\bpayment\b",
    r"\bcharged\b",
    r"\bbilling\b",
    r"\bsubscription\b",
    r"\brenewal\b",
    r"\brefund\b",
    r"\boverdue\b",
    r"扣费",
    r"账单",
    r"订阅",
    r"续费",
    r"退款",
    r"收款",
    r"付款",
    r"订单",
    r"收据",
    r"发票",
    r"电子发票",
]

SECURITY_PATTERNS = [
    r"security alert",
    r"unusual sign",
    r"verify your",
    r"验证码",
    r"异常登录",
    r"验证.*登录",
    r"verify.*sign.?in",
    r"new sign.?in",
]

MARKETING_PATTERNS = [
    r"\bsale\b",
    r"\bdiscount\b",
    r"% off",
    r"limited time",
    r"促销",
    r"优惠",
    r"免费领",
]

NEWSLETTER_SENDERS = [
    r"noreply@",
    r"newsletter",
    r"digest@",
    r"no-reply@",
]


def classify_text(subject: str, sender: str, snippet: str | None = None) -> Classification:
    blob = " ".join(filter(None, [subject, sender, snippet or ""])).lower()
    reasons: list[str] = []

    for pat in MONEY_PATTERNS:
        if re.search(pat, blob, re.I):
            reasons.append(f"matched money keyword: {pat}")
    if reasons:
        return Classification(RiskCategory.MONEY, 0, reasons[:5])

    for pat in SECURITY_PATTERNS:
        if re.search(pat, blob, re.I):
            reasons.append(f"matched security: {pat}")
    if reasons:
        return Classification(RiskCategory.SECURITY, 1, reasons[:5])

    snd = sender.lower()
    for pat in NEWSLETTER_SENDERS:
        if re.search(pat, snd, re.I):
            reasons.append(f"sender pattern: {pat}")
    if reasons and re.search(r"digest|daily|weekly|launch", blob, re.I):
        return Classification(RiskCategory.NEWSLETTER, 3, reasons[:5])

    for pat in MARKETING_PATTERNS:
        if re.search(pat, blob, re.I):
            reasons.append(f"marketing: {pat}")
    if reasons:
        return Classification(RiskCategory.MARKETING, 3, reasons[:5])

    if re.search(r"notification|alert|update", blob, re.I):
        return Classification(RiskCategory.TRANSACTIONAL, 2, ["generic notification wording"])

    return Classification(RiskCategory.OTHER, 4, ["no strong signal"])
