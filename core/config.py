"""Project-wide paths and constants shared across screens and the game.

Centralizing these means every module (regardless of how deep it sits in
the package tree) locates assets the same way, and every visual/content
tweak — swap an image, add an area, change the sponsor copy — happens in
exactly one place instead of being hunted down across files.
"""

import sys
from pathlib import Path

# core/config.py -> core/ -> project root when running from source.
# When frozen by PyInstaller (--onefile or --onedir), bundled data files
# are unpacked into sys._MEIPASS at runtime instead — __file__-based
# resolution isn't reliable inside a frozen build, so branch explicitly.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSETS_DIR = PROJECT_ROOT / "assets"

# --- Registration + Royal Room screen art ------------------------------------
BACKGROUND_IMAGE = ASSETS_DIR / "background0001.png"
FOOTER_IMAGE = ASSETS_DIR / "footer-0001.png"
BAND_IMAGE = ASSETS_DIR / "band.png"
ROYAL_ROOM_BACKGROUND = ASSETS_DIR / "background0002.png"
KEY_IMAGE = ASSETS_DIR / "key0001.png"

# --- Registration form validation --------------------------------------------
# Egyptian mobile numbers: 01 + [0,1,2,5] + 8 digits = 11 digits total

EGYPT_MOBILE_REGEX = r"^01[0125]\d{8}$"

# Simple, permissive email check — good enough to catch typos without being
# a strict RFC 5322 parser (which would reject plenty of valid addresses).
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

EGYPT_AREAS = [
    "Cairo", "Giza", "Alexandria", "Qalyubia", "Sharqia",
    "Dakahlia", "Gharbia", "Monufia", "Beheira", "Kafr El Sheikh",
    "Damietta", "Port Said", "Ismailia", "Suez", "North Sinai",
    "South Sinai", "Faiyum", "Beni Suef", "Minya", "Asyut",
    "Sohag", "Qena", "Luxor", "Aswan", "Red Sea", "New Valley", "Matrouh",
]

# --- Final screen sponsor content ---------------------------------------------
# Was hardcoded inside FinalScreen. Pulled out here so a sponsor swap is a
# one-line change instead of a UI-code edit.
PRODUCT_EMOJI = "🎀"
PRODUCT_NAME = "Perfectil Original"
PRODUCT_TAGLINE = "Beauty from within — Skin, Hair, Nails"

# --- Final (win reveal) screen art ---------------------------------------------
# The room reuses BACKGROUND_IMAGE (the same clean palace room the chest
# minigame stands in front of). FINAL_CHEST_IMAGE and FINAL_FOOTER_IMAGE are
# both exported at the *same* canvas size/aspect as that room and as each
# other, so they can be drawn at the exact same rect as the background with
# no extra alignment math — see FinalScreen.paintEvent(). FINAL_PRODUCT_IMAGE
# is a standalone product cutout (not canvas-aligned) positioned by fraction.
FINAL_CHEST_IMAGE = ASSETS_DIR / "box0003.png"
FINAL_FOOTER_IMAGE = ASSETS_DIR / "footer0003.png"
FINAL_PRODUCT_IMAGE = ASSETS_DIR / "product_box.png"

# Phase 2 of the final screen: once the chest reveal has held a moment,
# the backdrop crossfades to this lifestyle shot (chest/product/key/tagline
# all baked into the art itself, so the phase-1 overlays just fade out
# alongside the room). Same canvas size/aspect as BACKGROUND_IMAGE.
FINAL_LIFESTYLE_IMAGE = ASSETS_DIR / "background0003.png"