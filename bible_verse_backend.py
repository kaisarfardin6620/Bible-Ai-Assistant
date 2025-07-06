import os
import random
import logging
import asyncio
import aiohttp # For asynchronous HTTP requests
from openai import AsyncOpenAI, OpenAIError # Using AsyncOpenAI for async operations
from typing import Dict, List, Tuple, Optional, Any
from dotenv import load_dotenv
import re # For stripping HTML from Bible verse content

# Load environment variables from .env file
load_dotenv()

# --- Setup Logging ---
# Configure basic logging to output INFO level messages and above to the console.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- API KEYS & CONSTANTS ---
# Retrieve API keys from environment variables.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BIBLE_API_KEY = os.getenv("BIBLE_API_KEY")

# Validate that necessary environment variables are set.
if not OPENAI_API_KEY or not BIBLE_API_KEY:
    logger.critical("Missing required environment variables: OPENAI_API_KEY and/or BIBLE_API_KEY")
    # Raise an error to prevent the application from running without essential keys.
    raise ValueError("Missing required environment variables: OPENAI_API_KEY and/or BIBLE_API_KEY")

# Dictionary mapping Bible version names (short and long) to their API IDs.
# In a larger application, this might be loaded from a configuration file or database.
BIBLE_IDS = {
    "KJV": os.getenv("BIBLE_ID_KJV"),
    "KING JAMES VERSION": os.getenv("BIBLE_ID_KJV"),
    "WEB": os.getenv("BIBLE_ID_WEB"),
    "WORLD ENGLISH BIBLE": os.getenv("BIBLE_ID_WEB"),
    "ASV": os.getenv("BIBLE_ID_ASV"),
    "AMERICAN STANDARD VERSION": os.getenv("BIBLE_ID_ASV"),
    "ESV": os.getenv("BIBLE_ID_ESV"),
    "ENGLISH STANDARD VERSION": os.getenv("BIBLE_ID_ESV"),
    "NLT": os.getenv("BIBLE_ID_NLT"),
    "NEW LIVING TRANSLATION": os.getenv("BIBLE_ID_NLT"),
    "NIV": os.getenv("BIBLE_ID_NIV"),
    "NEW INTERNATIONAL VERSION": os.getenv("BIBLE_ID_NIV"),
    "RSVCE": os.getenv("BIBLE_ID_RSVCE"),
    "REVISED STANDARD VERSION CATHOLIC EDITION": os.getenv("BIBLE_ID_RSVCE"),
    "CSB": os.getenv("BIBLE_ID_CSB"),
    "CHRISTIAN STANDARD BIBLE": os.getenv("BIBLE_ID_CSB")
}

# Dictionary mapping full book names to their standard abbreviations used by the Bible API.
BOOK_ABBREVIATIONS = {
    "genesis": "GEN", "exodus": "EXO", "leviticus": "LEV", "numbers": "NUM", "deuteronomy": "DEU",
    "joshua": "JOS", "judges": "JDG", "ruth": "RUT", "1 samuel": "1SA", "2 samuel": "2SA",
    "1 kings": "1KI", "2 kings": "2KI", "1 chronicles": "1CH", "2 chronicles": "2CH",
    "ezra": "EZR", "nehemiah": "NEH", "esther": "EST", "job": "JOB", "psalms": "PSA",
    "proverbs": "PRO", "ecclesiastes": "ECC", "song of solomon": "SNG", "isaiah": "ISA",
    "jeremiah": "JER", "lamentations": "LAM", "ezekiel": "EZK", "daniel": "DAN",
    "hosea": "HOS", "joel": "JOL", "amos": "AMO", "obadiah": "OBA", "jonah": "JON",
    "micah": "MIC", "nahum": "NAM", "habakkuk": "HAB", "zephaniah": "ZEP", "haggai": "HAG",
    "zechariah": "ZEC", "malachi": "MAL", "matthew": "MAT", "mark": "MRK", "luke": "LUK",
    "john": "JHN", "acts": "ACT", "romans": "ROM", "1 corinthians": "1CO", "2 corinthians": "2CO",
    "galatians": "GAL", "ephesians": "EPH", "philippians": "PHP", "colossians": "COL",
    "1 thessalonians": "1TH", "2 thessalonians": "2TH", "1 timothy": "1TI", "2 timothy": "2TI",
    "titus": "TIT", "philemon": "PHM", "hebrews": "HEB", "james": "JAS", "1 peter": "1PE",
    "2 peter": "2PE", "1 john": "1JN", "2 john": "2JN", "3 john": "3JN", "jude": "JUD", "revelation": "REV"
}

# --- Initialize OpenAI client asynchronously ---
try:
    # Initialize the AsyncOpenAI client with the API key.
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
except OpenAIError as e:
    logger.critical(f"Failed to initialize OpenAI client: {e}")
    raise RuntimeError(f"Invalid OpenAI API key or configuration: {e}")

# --- Helper Function: Asynchronous Bible Verse Fetcher ---
async def get_bible_verse(book: str, chapter: str, verse: str, version: str) -> Dict[str, Optional[str]]:
    """
    Asynchronously fetches a Bible verse from the API.

    Args:
        book (str): The name of the Bible book (e.g., "John").
        chapter (str): The chapter number (e.g., "3").
        verse (str): The verse number (e.g., "16").
        version (str): The desired Bible version (e.g., "KJV", "NIV").

    Returns:
        Dict[str, Optional[str]]: A dictionary with "content" (the verse text) or "error" message.
    """
    bible_id = BIBLE_IDS.get(version.upper())
    if not bible_id:
        logger.warning(f"Unsupported Bible version requested: {version}")
        return {"content": None, "error": f"Sorry, the Bible version '{version}' is not supported."}
    
    book_key = book.lower().strip()
    book_abbr = BOOK_ABBREVIATIONS.get(book_key)
    if not book_abbr:
        logger.warning(f"Unrecognized Bible book: {book}")
        return {"content": None, "error": f"Book '{book}' not recognized. Please check the spelling."}
    
    reference = f"{book_abbr}.{chapter}.{verse}"
    url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{reference}"
    headers = {"api-key": BIBLE_API_KEY}
    
    logger.info(f"Attempting to fetch Bible verse: {url}")
    try:
        # Use aiohttp.ClientSession for making asynchronous HTTP requests.
        async with aiohttp.ClientSession() as session:
            # Set a timeout for the request to prevent hanging indefinitely.
            async with session.get(url, headers=headers, timeout=10) as response:
                # Raise an exception for HTTP errors (4xx or 5xx status codes).
                response.raise_for_status()
                data = await response.json()
                
                # The API typically returns content within 'data.content', which might contain HTML tags.
                content_html = data["data"]["content"]
                # Use regex to strip all HTML tags for cleaner text.
                clean_content = re.sub(r'<[^>]+>', '', content_html).strip()
                logger.info(f"Successfully fetched verse for {reference} ({version}).")
                return {"content": clean_content, "error": None}
    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP error fetching Bible verse {url}: Status {e.status}, Message: {e.message}")
        return {"content": None, "error": f"Error {e.status}: Failed to retrieve verse. Please check the reference or try again."}
    except aiohttp.ClientConnectionError as e:
        logger.error(f"Connection error fetching Bible verse {url}: {e}")
        return {"content": None, "error": "Connection error to Bible API. Please check your network or try again later."}
    except asyncio.TimeoutError:
        logger.error(f"Timeout fetching Bible verse {url}")
        return {"content": None, "error": "Bible API request timed out. The server might be busy."}
    except KeyError: # Handle cases where 'data' or 'content' keys might be missing in the JSON response.
        logger.error(f"Unexpected JSON structure from Bible API for {url}. Response data: {data}")
        return {"content": None, "error": "Unexpected response format from Bible API."}
    except Exception as e: # Catch any other unexpected errors during the process.
        logger.error(f"An unexpected error occurred in get_bible_verse for {url}: {e}", exc_info=True)
        return {"content": None, "error": f"An unexpected error occurred: {str(e)}"}

# --- List of Pre-defined Bible References for Random Selection ---
RANDOM_REFERENCES = [
    ("John", 3, 16),
    ("Psalm", 23, 1),
    ("Romans", 8, 28),
    ("Proverbs", 3, 5),
    ("Matthew", 5, 9),
    ("Philippians", 4, 13),
    ("Genesis", 1, 1),
    ("Isaiah", 40, 31),
    ("1 Corinthians", 13, 4),
    ("James", 1, 5)
]

# --- Main Backend-Ready Function ---
async def get_daily_encouragement_verse(user_preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asynchronously picks a random Bible verse based on user preferences (e.g., preferred version)
    and generates a concise summary using the OpenAI API. This function is designed to be
    called by a web backend API endpoint.

    Args:
        user_preferences (Dict[str, Any]): A dictionary containing user-specific preferences,
                                            such as {"bible_version": "NIV"}.

    Returns:
        Dict[str, Any]: A dictionary containing the verse reference, text, and summary.
                        It also includes an "error" key if any part of the process fails.
                        Example: {
                            "reference": "John 3:16",
                            "version": "NIV",
                            "verse_text": "For God so loved...",
                            "summary": "This verse highlights...",
                            "error": None
                        }
    """
    # Randomly select a Bible reference from the predefined list.
    book, chapter, verse = random.choice(RANDOM_REFERENCES)
    
    # Determine the preferred Bible version from user preferences, defaulting to KJV.
    preferred_version = user_preferences.get("bible_version", "KJV").upper()
    # Validate the preferred version against the list of supported versions.
    if preferred_version not in BIBLE_IDS:
        logger.warning(f"Invalid or unsupported Bible version '{preferred_version}' in user preferences. Defaulting to KJV.")
        preferred_version = "KJV" # Fallback to a default if the preferred version is not supported.

    logger.info(f"Attempting to fetch random verse: {book} {chapter}:{verse} in {preferred_version}")
    
    # Asynchronously fetch the Bible verse content.
    verse_lookup_result = await get_bible_verse(book, str(chapter), str(verse), preferred_version)
    
    verse_text = verse_lookup_result.get("content")
    verse_error = verse_lookup_result.get("error")

    # Handle cases where fetching the Bible verse failed.
    if verse_error:
        logger.error(f"Failed to fetch Bible verse {book} {chapter}:{verse} ({preferred_version}): {verse_error}")
        return {
            "reference": f"{book} {chapter}:{verse}",
            "version": preferred_version,
            "verse_text": None,
            "summary": None,
            "error": f"Could not retrieve verse: {verse_error}"
        }

    # Handle cases where the fetched verse content is unexpectedly empty.
    if not verse_text:
        logger.error(f"Bible verse content was empty for {book} {chapter}:{verse} ({preferred_version}). This should not happen if no error was returned.")
        return {
            "reference": f"{book} {chapter}:{verse}",
            "version": preferred_version,
            "verse_text": None,
            "summary": None,
            "error": "Retrieved verse content was empty, please try again."
        }

    # --- Generate a summary using OpenAI ---
    # Construct the prompt for the LLM to summarize the verse.
    prompt = f"Summarize this Bible verse in 100 words or less for encouragement and clarity, focusing on its spiritual message.\nVerse: {verse_text}"
    summary = None
    summary_error = None
    try:
        logger.info("Requesting summary generation from OpenAI.")
        # Make an asynchronous call to the OpenAI Chat Completions API.
        # Using 'gpt-4o' for its advanced capabilities.
        summary_resp_stream = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You summarize Bible verses for daily encouragement, focusing on spiritual insight and practical application."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5, # Controls randomness; lower for more focused summaries.
            max_tokens=150, # Limit the length of the summary.
            stream=True # Enable streaming for potentially faster initial response.
        )
        
        full_summary_content = ""
        # Iterate asynchronously over the streaming response chunks.
        async for chunk in summary_resp_stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    full_summary_content += content
        summary = full_summary_content.strip()
        logger.info("Successfully generated summary from OpenAI.")

    except OpenAIError as e:
        summary_error = f"OpenAI API error during summary generation: {e}"
        logger.error(f"OpenAI API error generating summary: {e}", exc_info=True)
    except Exception as e:
        summary_error = f"An unexpected error occurred during summary generation: {e}"
        logger.error(f"Unexpected error generating summary: {e}", exc_info=True)

    # Return the complete information about the verse and its summary.
    return {
        "reference": f"{book} {chapter}:{verse}",
        "version": preferred_version,
        "verse_text": verse_text,
        "summary": summary,
        "error": summary_error # Include any error encountered during summary generation.
    }

