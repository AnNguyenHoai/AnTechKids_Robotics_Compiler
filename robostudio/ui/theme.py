"""Small production UI design-system tokens for RoboStudio.

Phase 2 intentionally keeps styling modest and desktop-native. The goal is
consistent hierarchy and semantic state, not a decorative redesign.
"""
from __future__ import annotations


TEXT_PRIMARY = "#1f2937"
TEXT_SECONDARY = "#667085"
BORDER = "#d0d5dd"
SURFACE = "#ffffff"
SURFACE_MUTED = "#f8fafc"
PRIMARY = "#2563eb"
PRIMARY_HOVER = "#1d4ed8"
SUCCESS = "#15803d"
SUCCESS_BG = "#ecfdf3"
WARNING = "#b45309"
WARNING_BG = "#fffbeb"
ERROR = "#b42318"
ERROR_BG = "#fef3f2"
NEUTRAL = "#475467"
NEUTRAL_BG = "#f2f4f7"


def badge_style(tone: str) -> str:
    foreground, background = {
        "success": (SUCCESS, SUCCESS_BG),
        "warning": (WARNING, WARNING_BG),
        "error": (ERROR, ERROR_BG),
        "neutral": (NEUTRAL, NEUTRAL_BG),
    }.get(tone, (NEUTRAL, NEUTRAL_BG))
    return (
        f"color: {foreground}; background: {background}; border: 1px solid {foreground}; "
        "border-radius: 9px; padding: 2px 8px; font-weight: 600;"
    )


def primary_button_style() -> str:
    return (
        f"QPushButton {{ background: {PRIMARY}; color: white; border: none; border-radius: 6px; "
        "padding: 8px 14px; font-weight: 700; }} "
        f"QPushButton:hover {{ background: {PRIMARY_HOVER}; }} "
        "QPushButton:disabled { background: #cbd5e1; color: #64748b; }"
    )


def secondary_button_style() -> str:
    return (
        f"QPushButton {{ background: {SURFACE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; "
        "border-radius: 6px; padding: 7px 12px; }}"
    )


def card_style() -> str:
    return f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}"
