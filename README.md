# Preachly Backend

Preachly is a backend AI assistant designed to help users understand the Bible and Christian teachings. It provides empathetic, scripture-based responses, fetches Bible verses from the Scripture API, and supports user-friendly Bible version and book name input.

## Features
- Compassionate, knowledgeable AI assistant for Bible and Christian topics
- Fetches Bible verses using the Scripture API
- Supports multiple Bible versions (NIV, RSVCE, CSB, etc.)
- User-friendly book name and version input (e.g., "John 3:16 NIV")
- Robust error handling and logging
- Environment-based configuration for API keys and Bible IDs

## Setup
1. **Clone the repository and navigate to the project folder.**
2. **Create a `.env` file** with the following variables:
   ```
   OPENAI_API_KEY=your-openai-key
   BIBLE_API_KEY=your-bible-api-key
   BIBLE_ID_NIV=your-niv-id
   BIBLE_ID_RSVCE=your-rsvce-id
   BIBLE_ID_CSB=your-csb-id
   # Add more Bible IDs as needed
   ```
3. **Install dependencies:**
   ```sh
   pip install openai requests python-dotenv flask
   ```
4. **Run the Flask API server:**
   ```sh
   python the_bible_api.py
   ```
5. **Test the API:**
   - Use `test_bible_api.py` or Postman to send POST requests to `http://localhost:5001/preachly` with JSON:
     ```json
     {
       "user_input": "John 3:16 NIV",
       "conversation": null,
       "is_audio": false
     }
     ```

## File Overview
- `preachly_backend.py` — Core backend logic for Preachly
- `the_bible_api.py` — Flask API wrapper exposing `/preachly` endpoint
- `test_bible_api.py` — Script to test the API endpoint
- `.env` — Environment variables (not committed)

## Customization
- To add more Bible versions, add their IDs to `.env` and update the `BIBLE_IDS` dictionary in `preachly_backend.py`.
- To support more book name aliases, update the `BOOK_ABBREVIATIONS` dictionary.

## License
This project is for educational and non-commercial use. Please respect API provider terms.
