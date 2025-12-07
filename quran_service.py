"""
Quran translation service for retrieving verse translations from local JSON file.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Module-level translation storage
_quran_translations = None


def set_translations(translations: list):
    """Store the loaded translations."""
    global _quran_translations
    _quran_translations = translations
    logger.info(f"Translations loaded: {len(translations)} surahs")


def get_verse_translation(surah: int, verse: int) -> Optional[str]:
    """
    Get English translation for a specific verse.

    Args:
        surah: Surah number (1-114)
        verse: Verse number (1-based)

    Returns:
        Translation text or None if not found
    """
    if _quran_translations is None:
        logger.error("Translations not loaded!")
        return None

    # Validate surah number
    if surah < 1 or surah > 114:
        logger.error(f"Invalid surah number: {surah}")
        return None

    # Get surah array (0-indexed: surah 1 is at index 0)
    surah_verses = _quran_translations[surah - 1]

    # Validate verse number (0-indexed: verse 1 is at index 0)
    if verse < 1 or verse > len(surah_verses):
        logger.error(f"Invalid verse number: {surah}:{verse}")
        return None

    return surah_verses[verse - 1]


def format_three_verses_message(verses_data: list, translations: list) -> str:
    """
    Format 3 verses into a single combined message with translations.

    Args:
        verses_data: List of dicts with keys: 'surah', 'surah_name', 'verse'
        translations: List of 3 translation strings

    Returns:
        Formatted combined message string
    """
    if not verses_data or not translations:
        logger.error("Missing verses_data or translations")
        return ""

    if len(verses_data) != len(translations):
        logger.error(f"Mismatch: {len(verses_data)} verses but {len(translations)} translations")
        return ""

    # Build header
    header = "🌙 Today's Daily Quran Verses\n\n"

    # Build verse list
    verses_list = []
    for i, v in enumerate(verses_data):
        verse_header = f"📖 Surah {v['surah']}: {v['surah_name']} - Verse {v['verse']}"
        separator = "─" * 40
        translation = translations[i]
        verses_list.append(f"{verse_header}\n{separator}\n{translation}")

    # Combine with spacing
    combined_verses = "\n\n".join(verses_list)

    return header + combined_verses
