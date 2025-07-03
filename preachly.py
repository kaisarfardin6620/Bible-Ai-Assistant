import openai
import requests
import time
import os
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- API KEYS & CONSTANTS ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BIBLE_API_KEY = os.getenv("BIBLE_API_KEY")

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

# --- Initialize OpenAI client ---
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# --- System Prompt as a string ---
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

Keep your responses concise and under 100 words unless the user requests more detail.
"""

# --- Helper Functions ---
def get_bible_verse(book, chapter, verse, version):
    bible_id = BIBLE_IDS.get(version.upper())
    
    if not bible_id:
        return f"Sorry, the Bible version '{version}' is not supported. Please choose from: {', '.join(BIBLE_IDS.keys())}."

    reference = f"{book}.{chapter}.{verse}".lower()
    url = f"https://api.scripture.api.bible/v1/bibles/{bible_id}/verses/{reference}"
    headers = {"api-key": BIBLE_API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data["data"]["content"]
    else:
        return f"Sorry, could not retrieve the verse (Error {response.status_code})."


# --- Mock User Data Function ---
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
        "bible_version": "NEW INTERNATIONAL VERSION"  # e.g., "NEW INTERNATIONAL VERSION", "REVISED STANDARD VERSION CATHOLIC EDITION", "CHRISTIAN STANDARD BIBLE"
    }
 
response_cache = {}

def chat_with_bible_bot(conversation):
    # Use a tuple of the last 3 messages as a cache key
    cache_key = tuple((msg["role"], msg["content"]) for msg in conversation[-3:])
    if cache_key in response_cache:
        cached_reply = response_cache[cache_key]
        print(cached_reply, end="", flush=True)  # Stream cached reply
        print()  # newline after streaming ends
        return cached_reply
    try:
        # --- Inject user data into the system prompt for personalization ---
        user_data = get_mock_user_data()

        # Format tone choices with descriptions for the prompt
        tone_lines = []
        for tone in user_data['tone_choices']:
            tone_lines.append(f"  - {tone['name']}: {tone['description']} (Example: {tone['example']})")
        # Bible familiarity
        familiarity = user_data['bible_familiarity']
        personalized_system_prompt = SYSTEM_PROMPT + "\n" + (
            f"\nUser Profile:\n"
            f"- Faith Goal: {user_data['faith_goal']}\n"
            f"- Denomination: {user_data['denomination']}\n"
            f"- Personalization Reasons: {', '.join(user_data['personalization_reasons'])}\n"
            f"- Tone Choices:\n" + "\n".join(tone_lines) + "\n"
            f"- Bible Familiarity: {familiarity['level']} — {familiarity['description']}\n"
            f"- Bible Version: {user_data['bible_version']}\n"
        )

        # Replace the system prompt in the conversation with the personalized one
        conversation_with_profile = conversation.copy()
        if conversation_with_profile and conversation_with_profile[0]["role"] == "system":
            conversation_with_profile[0]["content"] = personalized_system_prompt

        response_stream = client.chat.completions.create(
            model="gpt-4-turbo",  # or your preferred GPT-4 Turbo model
            messages=conversation_with_profile,
            temperature=0.7,
            max_tokens=300,
            stream=True
        )
        assistant_reply = ""
        for chunk in response_stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                print(delta.content, end="", flush=True)  # streaming print chunk-by-chunk
                assistant_reply += delta.content
        print()  # newline after streaming ends
        response_cache[cache_key] = assistant_reply
        return assistant_reply
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, something went wrong. Please try again later."

# --- Main CLI Loop ---
def main():
    conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("🙏 Welcome! I'm here to help you explore the Bible and faith. Type 'exit' when you want to end our conversation.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye! May you be blessed.")
            break

        conversation.append({"role": "user", "content": user_input})

        bot_reply = chat_with_bible_bot(conversation)
        # Do NOT print the bot reply again here, streaming already printed it
        # print("Bot:", bot_reply)  # <-- removed to avoid duplicate printing

        conversation.append({"role": "assistant", "content": bot_reply})

        # Check if bot is asking for clarification about Bible verses
        clarifying_keywords = ["did you mean", "which passage", "please specify", "full reference", "book", "chapter", "verse", "version"]

        if any(keyword in bot_reply.lower() for keyword in clarifying_keywords):
            next_input = input("You (please specify full reference or say 'no'): ").strip()

            if next_input.lower() == "no":
                # Acknowledge user saying no and continue
                bot_ack = "No problem! If you want to talk about anything else, just ask."
                print("Bot:", bot_ack)
                conversation.append({"role": "user", "content": next_input})
                conversation.append({"role": "assistant", "content": bot_ack})
                continue  # skip the Bible reference parsing below

            conversation.append({"role": "user", "content": next_input})

            try:
                parts = next_input.split()
                if len(parts) < 2:
                    raise ValueError("Please provide both the book and chapter:verse.")

                if parts[-1].upper() in BIBLE_IDS:
                    version = parts[-1].upper()
                    parts = parts[:-1]
                else:
                    raise ValueError("Bible version missing or not supported. Please include version like NIV, CSB, or RSVCE.")

                if len(parts) < 2:
                    raise ValueError("Incomplete Bible reference. Please specify book and chapter:verse.")

                chapter_verse = parts[-1]
                book = " ".join(parts[:-1])

                if ":" not in chapter_verse:
                    raise ValueError("Chapter and verse must be separated by a colon ':'. For example: 3:16.")

                chapter, verse = chapter_verse.split(":")

                verse_text = get_bible_verse(book, chapter, verse, version)
                print("\n📖 Verse:", verse_text, "\n")
                conversation.append({"role": "assistant", "content": verse_text})
                # Remove the last user clarification input so it doesn't get processed again
                conversation.pop()  # Remove the last user message
                continue
            except ValueError as ve:
                error_msg = f"Sorry, {ve}"
                print(error_msg)
                conversation.append({"role": "assistant", "content": error_msg})
                conversation.pop()  # Remove the last user message
                continue
            except Exception:
                error_msg = "Sorry, I couldn't understand that reference. Please specify like 'John 3:16 NIV'."
                print(error_msg)
                conversation.append({"role": "assistant", "content": error_msg})
                conversation.pop()  # Remove the last user message
                continue

if __name__ == "__main__":
    main()
