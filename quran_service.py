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

    # Get first and last verse numbers for the header
    first_verse = verses_data[0]
    last_verse = verses_data[-1]

    # Build header with verse range
    header = f"🌙 Today's Daily Quran Verses\n\n"

    # Check if all verses are from the same surah
    all_same_surah = all(v['surah'] == first_verse['surah'] for v in verses_data)

    if all_same_surah:
        # Simple case: all verses from same surah
        header += f"Surah {first_verse['surah']}: {first_verse['surah_name']} - Verse {first_verse['verse']} to {last_verse['verse']}\n"
    else:
        # Cross-surah case: show each verse individually
        verse_refs = []
        for v in verses_data:
            verse_refs.append(f"{v['surah']}:{v['verse']}")
        header += f"Verses: {', '.join(verse_refs)}\n"

    header += "---------------------------------------------------------\n"

    # Build translation list (numbered)
    translation_lines = []
    for i, translation in enumerate(translations, 1):
        translation_lines.append(f"{translation}")

    # Combine translations with spacing
    combined_translations = "\n\n".join(translation_lines)

    return header + combined_translations
