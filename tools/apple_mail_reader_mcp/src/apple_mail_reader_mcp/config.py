"""Runtime config — default is Mail.app + JXA only (no Full Disk Access)."""

from __future__ import annotations

import os


def use_envelope_index() -> bool:
    """Opt-in fast path via ~/Library/Mail Envelope Index (needs Full Disk Access)."""
    return os.environ.get("APPLE_MAIL_USE_ENVELOPE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
