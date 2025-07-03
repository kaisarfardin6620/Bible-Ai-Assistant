import os
import requests
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("BIBLE_API_KEY")
if not api_key:
    raise RuntimeError("BIBLE_API_KEY not set in environment variables.")

url = "https://api.scripture.api.bible/v1/bibles"
headers = {"api-key": api_key}
response = requests.get(url, headers=headers)
data = response.json()

# List of abbreviations or names you want
wanted = {
    "KJV": "King James Version",
    "WEB": "World English Bible",
    "ASV": "American Standard Version",
    "ESV": "English Standard Version",
    "NLT": "New Living Translation"
}

for bible in data.get("data", []):
    abbr = bible.get("abbreviation", "").upper()
    name = bible.get("name", "")
    for key, wanted_name in wanted.items():
        if abbr == key or wanted_name.lower() in name.lower():
            print(f"{key}: {bible['id']} ({name})")