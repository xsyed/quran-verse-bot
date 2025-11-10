"""
OpenAI API integration for generating verse explanations.
"""

import os
from typing import Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# Client will be initialized lazily on first use
_client = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client instance."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


def generate_verse_explanation(surah: int, surah_name: str, verse: int) -> Optional[str]:
    """
    Generate transliteration, translation, and explanation for a verse using OpenAI.

    Args:
        surah: Surah number
        surah_name: Surah name in English
        verse: Verse number

    Returns:
        Formatted string with the verse explanation or None if error
    """
    prompt = f"""You are a knowledgeable Islamic scholar providing brief, accessible explanations of Qur'an verses for daily reflection.

Surah: {surah} - {surah_name}
Verse: {verse}

Provide the following three sections in this exact order:

1) Transliteration of this verse in English
2) English Translation (clear and simple)
3) Context + Understanding (max 50 words) explaining:
  - the core message and wisdom of this verse
  - spiritual and practical daily life lessons
  - simple language suitable for WhatsApp message format
  - respectful, uplifting tone
  - do NOT repeat the verse text inside this explanation (you already provided it above)

Keep everything concise, gentle, spiritually beneficial, and theologically accurate."""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable Islamic scholar providing accessible explanations of Qur'an verses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=1,
            max_tokens=300
        )

        explanation = response.choices[0].message.content.strip()
        logger.info(f"Generated explanation for Surah {surah}:{verse}")
        return explanation

    except Exception as e:
        logger.error(f"Error generating explanation for Surah {surah}:{verse}: {e}")
        return None


def generate_three_verses_explanation(verses_data: list) -> Optional[list]:
    """
    Generate explanations for 3 verses in a single API call.

    Args:
        verses_data: List of dicts with keys: 'surah', 'surah_name', 'verse'
                     Example: [
                         {'surah': 1, 'surah_name': 'Al-Fatihah', 'verse': 1},
                         {'surah': 1, 'surah_name': 'Al-Fatihah', 'verse': 2},
                         {'surah': 1, 'surah_name': 'Al-Fatihah', 'verse': 3}
                     ]

    Returns:
        List of explanation strings (one per verse) or None if error
    """
    if not verses_data or len(verses_data) != 3:
        logger.error(f"Invalid verses_data: expected 3 verses, got {len(verses_data) if verses_data else 0}")
        return None

    # Build the prompt for all 3 verses
    verses_info = "\n\n".join([
        f"VERSE {i+1}:\nSurah: {v['surah']} - {v['surah_name']}\nVerse: {v['verse']}"
        for i, v in enumerate(verses_data)
    ])

    prompt = f"""You are a knowledgeable Islamic scholar providing brief, accessible explanations of Qur'an verses for daily reflection.

{verses_info}

Provide the content (not per-verse, but grouped by type):

1 - TRANSLITERATIONS:
-------------------------------------
Provide transliterations for all 3 verses, in a paragraph separated by period.

2 - ENGLISH TRANSLATIONS: 
-------------------------------------
Provide English translations for all 3 verses, in a paragraph separated by period.

3 - CONTEXT & UNDERSTANDING:
-------------------------------------
Provide context and understanding for all 3 verses combined (50 words total):
  - the core message and wisdom connecting these verses
  - spiritual and practical daily life lessons
  - simple language suitable for WhatsApp message format
  - respectful, uplifting tone
  - do NOT repeat the verse texts inside this explanation (you already provided them above)

IMPORTANT:- Do not send the text in markdown styling. like ## or ***. Just send as normal text.

Keep everything concise, gentle, spiritually beneficial, and theologically accurate."""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable Islamic scholar providing accessible explanations of Qur'an verses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=1,
            max_tokens=900  # Increased for 3 verses
        )

        full_response = response.choices[0].message.content.strip()

        # Split by the separator to get the 3 sections
        sections = full_response.split("---SECTION_SEPARATOR---")
        sections = [sec.strip() for sec in sections if sec.strip()]

        if len(sections) != 3:
            logger.warning(f"Expected 3 sections but got {len(sections)}, using raw response")
            # If separator didn't work, return the full response
            return [full_response]

        # Return the three sections: [transliterations, translations, context]
        logger.info(f"Generated content for {len(verses_data)} verses in 3 sections")
        return sections

    except Exception as e:
        logger.error(f"Error generating batch explanations: {e}")
        return None


def format_verse_message(surah: int, surah_name: str, verse: int, explanation: str) -> str:
    """
    Format the verse message for sending to users.

    Args:
        surah: Surah number
        surah_name: Surah name in English
        verse: Verse number
        explanation: Generated explanation from OpenAI

    Returns:
        Formatted message string
    """
    header = f"📖 Surah {surah}: {surah_name} - Verse {verse}\n"
    separator = "─" * 40 + "\n\n"

    return header + separator + explanation


def format_three_verses_message(verses_data: list, sections: list) -> str:
    """
    Format all 3 verses into a single combined message with grouped sections.

    Args:
        verses_data: List of dicts with keys: 'surah', 'surah_name', 'verse'
        sections: List of 3 strings: [transliterations, translations, context]

    Returns:
        Formatted combined message string
    """
    if len(sections) == 1:
        # Fallback: separator didn't work, just display raw content
        logger.warning("Using fallback formatting for single section")
        header = "🌙 Today's Daily Quran Verses\n\n"
        verses_list = "\n".join([
            f"📖 Surah {v['surah']}: {v['surah_name']} - Verse {v['verse']}"
            for v in verses_data
        ])
        return header + verses_list + "\n\n" + "─" * 40 + "\n\n" + sections[0]

    if len(sections) != 3:
        logger.error(f"Expected 3 sections but got {len(sections)}")
        return ""

    # Build header with verse references
    header = "🌙 Today's Daily Quran Verses\n\n"
    verses_list = "\n".join([
        f"📖 Surah {v['surah']}: {v['surah_name']} - Verse {v['verse']}"
        for v in verses_data
    ])

    # Build the message with the three sections
    message_parts = [
        header,
        verses_list,
        "\n\n" + "═" * 40 + "\n\n",
        "🔤 TRANSLITERATIONS:\n\n",
        sections[0],  # All transliterations
        "\n\n" + "═" * 40 + "\n\n",
        "📖 ENGLISH TRANSLATIONS:\n\n",
        sections[1],  # All translations
        "\n\n" + "═" * 40 + "\n\n",
        "💡 CONTEXT & UNDERSTANDING:\n\n",
        sections[2]   # Combined context
    ]

    return "".join(message_parts)
