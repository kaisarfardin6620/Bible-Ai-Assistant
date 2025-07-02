import os
import re
import logging
from functools import lru_cache
import openai
import requests
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
load_dotenv()

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- API KEYS & CONSTANTS ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BIBLE_API_KEY = os.getenv("BIBLE_API_KEY")

# Validate environment variables
if not OPENAI_API_KEY or not BIBLE_API_KEY:
    raise ValueError("Missing required environment variables: OPENAI_API_KEY and/or BIBLE_API_KEY")

BIBLE_IDS = {
    # Short and long names for each supported version, all upper-case for consistency
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

# --- System Prompt ---
SYSTEM_PROMPT = """
You are a compassionate and knowledgeable assistant designed to help people understand the Bible and Christian teachings.
When the user expresses doubt or disbelief in God or Jesus, respond with empathy but also share a thoughtful, scripture-based reply.
For example, mention relevant Bible verses like Psalm 14:1 which says, "The fool hath said in his heart, There is no God." Balance respect with gentle biblical teaching.
Your audience may include people who do not believe in God, are new to Christianity, or come from different cultural and religious backgrounds.
Always communicate with kindness, patience, and respect, avoiding judgment or assumptions about the user’s beliefs.

When answering questions:
Provide clear, simple explanations that anyone can understand, avoiding complicated theological terms unless you define them gently.
Use relevant Bible verses to support your answers. When possible, include passages from Protestant, Catholic, or Orthodox Bibles based on the user’s preference or the context.
If the user asks for specific Bible verses, provide the exact verse text along with the book, chapter, and verse reference.
If the user does not specify a Bible version or preference, gently invite them to specify which version they prefer (e.g., NIV, RSVCE, CSB) to ensure accurate responses.
If a Bible reference is unclear or incomplete, kindly ask the user to clarify the full book, chapter, verse, and version to avoid misunderstandings or incorrect quotes.
When discussing differences between Christian traditions, explain these differences factually, neutrally, and without bias or favoritism.
Help users connect Biblical teachings to everyday life by offering practical examples or reflections.
When appropriate, encourage spiritual reflection, hope, forgiveness, love, and peace, but do so respectfully without pressuring belief.
If the user provides audio or voice input, process it with care: acknowledge their message, confirm understanding, and respond thoughtfully as you would with text input.
If a question is about complex doctrine or is beyond your scope:
Admit politely that the question is difficult or outside your expertise.
Offer to help find relevant Bible passages or direct the user to trusted resources for further study.
Remember, your main goal is to be a gentle guide, making the Bible’s message accessible, meaningful, and relevant for everyone regardless of their background or beliefs.
"""

# --- Initialize OpenAI client ---
client = openai.OpenAI(api_key=OPENAI_API_KEY)


# --- Helper Functions (remain unchanged) ---
def get_bible_verse(book: str, chapter: str, verse: str, version: str) -> Dict[str, Optional[str]]:
    bible_id = BIBLE_IDS.get(version.upper())
    if not bible_id:
        return {"content": None, "error": f"Sorry, the Bible version '{version}' is not supported."}
    book_key = book.lower().strip()
    book_abbr = BOOK_ABBREVIATIONS.get(book_key)
    if not book_abbr:
        return {"content": None, "error": f"Book '{book}' not recognized. Please check the spelling."}
    reference = f"{book_abbr}.{chapter}.{verse}"
    url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{reference}"
    headers = {"api-key": BIBLE_API_KEY}
    logger.info(f"Requesting: {url} with {headers}")
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return {"content": response.json()["data"]["content"], "error": None}
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error: {str(e)}, Response: {response.text}")
        return {"content": None, "error": f"Error {response.status_code}: {response.text}"}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"content": None, "error": f"Unexpected error: {str(e)}"}

@lru_cache(maxsize=1000)
def chat_with_bible_bot(conversation: tuple) -> str:
    """
    Generates a response from the OpenAI API for a given conversation, with caching.
    """
    logger.info(f"Processing conversation with {len(conversation)} messages")
    try:
        response_stream = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": role, "content": content} for role, content in conversation],
            temperature=0.7,
            max_tokens=300,
            stream=True
        )
        assistant_reply = ""
        for chunk in response_stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                assistant_reply += delta.content
        logger.info("Generated response successfully")
        return assistant_reply
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return f"Sorry, an error occurred with the AI service: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_bible_bot: {str(e)}")
        return "Sorry, something went wrong. Please try again later."

def parse_bible_reference(input_text: str) -> Dict[str, Optional[str]]:
    """
    Parses user input for a Bible reference in a strict "Book chapter:verse VERSION" format.
    """
    pattern = r"^(?:([1-3]?\s?[A-Za-z]+)\s+(\d+):(\d+)\s+([A-Za-z\s]+))$"
    match = re.match(pattern, input_text.strip(), re.IGNORECASE)
    
    if not match:
        return {
            "success": False,
            "content": None,
            "error": "Not a direct Bible verse lookup format (e.g., 'John 3:16 NIV')"
        }
    
    book, chapter, verse, version = match.groups()
    
    if not chapter.isdigit() or not verse.isdigit():
        return {
            "success": False,
            "content": None,
            "error": "Chapter and verse must be numbers (e.g., '3:16')."
        }
    
    result = get_bible_verse(book, chapter, verse, version)
    
    return {
        "success": result["error"] is None,
        "content": result["content"],
        "error": result["error"]
    }

# Removed initialize_conversation as a standalone function because it's now internal


def get_mock_user_data():
    """
    Returns a mock user data dictionary representing onboarding selections.
    This can be replaced with real user input collection in production.
    """
    return {
        # Faith Goal logic: set based on user answers (example: 'Confidence', 'Scripture Knowledge', 'Inspiration')
        "faith_goal": "Confidence",  # or "Scripture Knowledge", "Inspiration"
        # Onboarding questions and options
        "onboarding_questions": [
            {
                "question": "What’s holding you back from confidently living and sharing your faith?",
                "options": [
                    {"text": "I feel unsure how to respond to questions or doubts about my faith.", "goal": "Confidence"},
                    {"text": "I struggle to find the right words to share scripture effectively.", "goal": "Scripture Knowledge"},
                    {"text": "I feel I need a deeper connection to God’s word before I can inspire others.", "goal": "Inspiration"}
                ]
            },
            {
                "question": "How do you hope to grow in your walk with God?",
                "options": [
                    {"text": "I want to learn how to speak about my faith with confidence and clarity.", "goal": "Confidence"},
                    {"text": "I want to strengthen my understanding of scripture and apply it to my life.", "goal": "Scripture Knowledge"},
                    {"text": "I want to inspire and encourage others through my faith journey.", "goal": "Inspiration"}
                ]
            },
            {
                "question": "What would help you feel more equipped to achieve your faith goals?",
                "options": [
                    {"text": "Practical tools to respond to objections and questions about faith.", "goal": "Confidence"},
                    {"text": "Daily scripture insights that I can share with others or reflect on.", "goal": "Inspiration"},
                    {"text": "Clear and inspired guidance rooted in scripture.", "goal": "Scripture Knowledge"}
                ]
            }
        ],
        # Denominations
        "denomination": "Protestant",  # e.g., "Protestant", "Catholic", "Orthodox", "Baptist", etc.
        "denomination_options": [
            "Catholic", "Protestant", "Baptist", "Nondenominational", "Methodist", "Pentecostal",
            "Lutheran", "Evangelical", "Adventist", "Orthodox", "Other"
        ],
        # Bible Versions
        "bible_version": "KJV",  # e.g., "KJV", "WEB", "ASV", "ESV", "NLT"
        "bible_version_options": [
            "KJV (King James Version)",
            "WEB (World English Bible)",
            "ASV (American Standard Version)",
            "NIV (New International Version)",
            "RSVCE (Revised Standard Version Catholic Edition)",
            "CSB (Christian Standard Bible)"
        ],
        # Personalization reasons (legacy, can be mapped to faith goals)
        "personalization_reasons": [
            "Fear of sharing faith",
            "Struggling to study",
            "Needing deeper connection"
        ],
        "tone_choices": [
            {
                "name": "Clear and Hopeful",
                "description": "Simple, direct, and encouraging. Speaks to God’s love and faithfulness in an easily understood way.",
                "example": "God allows us to choose because He loves us deeply. Even in our struggles, His grace is always enough."
            },
            {
                "name": "Dynamic and Powerful",
                "description": "Emotive, bold, and filled with vivid imagery. Designed to inspire and energize.",
                "example": "Sin may exist, but so does God’s unstoppable power to redeem, restore, and turn every story into a victory."
            },
            {
                "name": "Practical and Everyday",
                "description": "Grounded and solution-oriented, focusing on how faith applies to daily life.",
                "example": "Sometimes life feels messy, but God uses even our mistakes to shape us and teach us how to walk in His ways."
            },
            {
                "name": "Encouraging and Purposeful",
                "description": "Focuses on meaning and growth through challenges, using affirming and positive language.",
                "example": "It’s not always easy to understand, but God allows challenges so we can grow stronger in faith and closer to Him."
            },
            {
                "name": "Uplifting and Optimistic",
                "description": "Highlights hope and joy even in adversity, emphasizing God’s ongoing provision.",
                "example": "Even in a broken world, God’s love shines through. His plan for good will always outweigh the pain we see now."
            },
            {
                "name": "Scholarly and Rational",
                "description": "Appeals to logic and reason, using well-structured arguments and historical/theological insights.",
                "example": "Sin entered through humanity’s choices, but God’s plan through Jesus shows us the depth of His justice and mercy."
            },
            {
                "name": "Warm and Relatable",
                "description": "Conversational, empathetic, and emotionally resonant. Speaks to the heart with compassion.",
                "example": "That’s a tough question—it’s okay to wrestle with it. What matters most is knowing God is with you, no matter what."
            },
            {
                "name": "Passionate and Empowering",
                "description": "Focused on spiritual growth and perseverance, emphasizing strength and action.",
                "example": "Sin doesn’t define us—God’s purpose does. You have the power to walk boldly in the freedom He’s given you."
            }
        ],
        "bible_familiarity_options": [
            {
                "level": "None",
                "title": "New to the Word? No problem!",
                "description": "Simplified Responses\nPreachly will break things down in an easy-to-understand way, offering clear, simple explanations to help you build a strong foundation."
            },
            {
                "level": "A Little",
                "title": "A great foundation! Let’s go deeper",
                "description": "You have some knowledge, and we’ll build on it!"
            },
            {
                "level": "A Lot",
                "title": "Ready for the deep dive?",
                "description": "Multi-Argumentation Responses\nPreachly will provide multi-layered explanations, exploring different perspectives, theological arguments, and scriptural connections to help you sharpen your understanding."
            }
        ],
        "bible_familiarity": {
            "level": "A Little",
            "title": "A great foundation! Let’s go deeper",
            "description": "You have some knowledge, and we’ll build on it!"
        },
        "bible_version": "NEW INTERNATIONAL VERSION"  # e.g., "NEW INTERNATIONAL VERSION", "REVISED STANDARD VERSION CATHOLIC EDITION", "CHRISTIAN STANDARD BIBLE"
    }


def get_preachly_response(user_input: str, conversation: Optional[List[Dict[str, str]]] = None, is_audio: bool = False) -> Tuple[str, List[Dict[str, str]]]:
    """
    Processes a user's message and returns the AI's response and updated conversation.
    If no conversation history is provided, it initializes a new one.

    Args:
        user_input (str): The user's input message.
        conversation (Optional[List[Dict[str, str]]]): The current conversation history.
                                                      If None, a new conversation is started.
        is_audio (bool): Whether the input is from audio transcription.

    Returns:
        Tuple[str, List[Dict[str, str]]]: The AI's response and the updated conversation.
    """
    # Initialize conversation if not provided (for the first turn)
    if conversation is None:
        conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add user message to conversation
    conversation.append({"role": "user", "content": user_input})
    
    # Handle audio input
    audio_ack = "(Received as a transcribed voice message.)\n\n" if is_audio else ""
    
    bot_reply = ""
    
    # First, try to parse as a direct Bible reference
    ref_result = parse_bible_reference(user_input)
    
    if ref_result["success"]:
        # If it's a direct, successful Bible verse lookup, return just the verse content
        bot_reply = audio_ack + ref_result["content"]
    else:
        # If not a direct verse lookup, or if the lookup failed,
        # delegate to the LLM to understand the natural language query.
        # Prepend the error from parse_bible_reference only if there was an actual error getting the verse,
        # but not if it just failed to match the strict regex.
        prepend_error_message = ""
        if ref_result["error"] and "Not a direct Bible verse lookup format" not in ref_result["error"]:
            prepend_error_message = ref_result["error"] + "\n\n"
            
        # Use cached conversation for AI response
        # Using only the last few messages for the LLM call to manage token usage
        # IMPORTANT: The system prompt MUST always be included as the first message
        # So, if conversation has more than 3 messages (system + user + assistant + user),
        # we still ensure the system prompt is always there.
        messages_for_llm = [conversation[0]] + conversation[-3:] # System prompt + last 3 turns
        conversation_tuple = tuple((msg["role"], msg["content"]) for msg in messages_for_llm)
        
        llm_response = chat_with_bible_bot(conversation_tuple)
        
        bot_reply = audio_ack + prepend_error_message + llm_response
    
    # Update conversation with AI response
    conversation.append({"role": "assistant", "content": bot_reply})
    return bot_reply, conversation

