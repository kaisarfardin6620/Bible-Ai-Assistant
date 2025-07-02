import random
import datetime
from preachly_backend import get_mock_user_data, get_bible_verse
import openai
import os
from dotenv import load_dotenv
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Initialize OpenAI client ---
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Allowed Bible versions and their IDs (must match .env and backend)
ALLOWED_BIBLE_VERSIONS = {
    "KJV": os.getenv("BIBLE_ID_KJV"),
    "WEB": os.getenv("BIBLE_ID_WEB"),
    "ASV": os.getenv("BIBLE_ID_ASV"),
    "NIV": os.getenv("BIBLE_ID_NIV"),
    "RSVCE": os.getenv("BIBLE_ID_RSVCE"),
    "CSB": os.getenv("BIBLE_ID_CSB")
}

# List of references to pick from (expand as needed)
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

def get_random_verse(user_data):
    """
    Picks a random reference from the list and fetches the verse in the selected version.
    """
    book, chapter, verse = random.choice(RANDOM_REFERENCES)
    version = user_data.get("bible_version", "KJV")
    verse_text = get_bible_verse(book, str(chapter), str(verse), version)
    if isinstance(verse_text, dict):
        verse_text = verse_text.get("content") or str(verse_text)
    # Generate a summary
    prompt = f"Summarize this Bible verse in 100 words or less for encouragement and clarity.\nVerse: {verse_text}"
    try:
        summary_resp = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You summarize Bible verses for daily encouragement."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=150
        )
        summary = summary_resp.choices[0].message.content.strip()
    except Exception as e:
        summary = f"(Could not generate summary: {e})"
    return {
        "reference": f"{book} {chapter}:{verse}",
        "verse_text": verse_text,
        "summary": summary
    }

if __name__ == "__main__":
    # Interactive CLI to choose Bible version
    print("Choose your preferred Bible version:")
    version_keys = list(ALLOWED_BIBLE_VERSIONS.keys())
    for idx, v in enumerate(version_keys, 1):
        print(f"{idx}. {v}")
    while True:
        try:
            choice = int(input("Enter the number of your choice: ").strip())
            if 1 <= choice <= len(version_keys):
                selected_version = version_keys[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(version_keys)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Use mock user data but override the bible_version
    user_data = get_mock_user_data()
    user_data["bible_version"] = selected_version
    print("\nFetching your verse... Please wait.\n", flush=True)
    verse_info = get_random_verse(user_data)
    print(f"\nVerse: {verse_info['reference']} ({selected_version})", flush=True)
    print(f"Text: {verse_info['verse_text']}", flush=True)
    print(f"Summary: {verse_info.get('summary', '(No summary available.)')}", flush=True)
