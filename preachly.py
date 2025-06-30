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
    "NEW INTERNATIONAL VERSION": os.getenv("BIBLE_ID_NIV"),
    "REVISED STANDARD VERSION CATHOLIC EDITION": os.getenv("BIBLE_ID_RSVCE"),
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
        response_stream = client.chat.completions.create(
            model="gpt-4-turbo",  # or your preferred GPT-4 Turbo model
            messages=conversation,
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
