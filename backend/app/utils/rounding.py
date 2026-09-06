"""
Shared rounding helpers for goal suggestions.

Keeps raw BMR/macro math numbers out of the UI — raw values like 1873 kcal
or 127 g protein are technically correct but look unpolished to users.

Usage:
    from app.services.strategies.rounding import nice_calories, nice_macros

All strategy implementations should pipe their outputs through these.
"""


def nice_calories(val: int | float) -> int:
    """Round to nearest 50. 1873 → 1850, 2115 → 2100."""
    return round(val / 50) * 50


def nice_macro(val: int | float) -> int:
    """Round to nearest 5. 127 → 125, 83 → 85."""
    return round(val / 5) * 5
