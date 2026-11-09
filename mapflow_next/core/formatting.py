"""Numbers and dates the way the UI shows them. Pure Python."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def km2(value: float) -> str:
    if value >= 100:
        return f"{value:,.0f} km²"
    if value >= 0.1:
        return f"{value:,.2f} km²"
    return f"{value:,.3f} km²"


def credits(value: Optional[int]) -> str:
    return "—" if value is None else f"{value:,}"


def per_km2(value: float) -> str:
    return f"{value:g} cr/km²"


def when(moment: Optional[datetime], now: Optional[datetime] = None) -> str:
    if moment is None:
        return ""
    now = now or datetime.now(timezone.utc)
    local = moment.astimezone()
    days = (now.astimezone().date() - local.date()).days
    if days == 0:
        minutes = int((now - moment).total_seconds() // 60)
        if minutes < 1:
            return "just now"
        if minutes < 60:
            return f"{minutes} min ago"
        return f"today {local:%H:%M}"
    if days == 1:
        return f"yesterday {local:%H:%M}"
    if local.year == now.year:
        return f"{local.day} {local:%b}"
    return f"{local.day} {local:%b %Y}"


def size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:,.0f} {unit}" if unit in ("B", "KB") else f"{value:,.1f} {unit}"
        value /= 1024
    return f"{num_bytes} B"
