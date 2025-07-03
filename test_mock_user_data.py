from preachly_backend import get_mock_user_data

if __name__ == "__main__":
    user_data = get_mock_user_data()
    print("--- MOCK USER DATA ---")
    for key, value in user_data.items():
        print(f"{key}: {value}\n")
    # Print onboarding questions in a readable way
    print("\nOnboarding Questions:")
    for q in user_data["onboarding_questions"]:
        print(f"- {q['question']}")
        for opt in q['options']:
            print(f"    * {opt['text']} (goal: {opt['goal']})")
    # Print tone choices
    print("\nTone Choices:")
    for tone in user_data["tone_choices"]:
        print(f"- {tone['name']}: {tone['description']} (Example: {tone['example']})")
    # Print Bible familiarity options
    print("\nBible Familiarity Options:")
    for fam in user_data["bible_familiarity_options"]:
        print(f"- {fam['level']}: {fam['title']} - {fam['description']}")
    # Print selected Bible familiarity
    if "bible_familiarity" in user_data:
        fam = user_data["bible_familiarity"]
        print(f"\nSelected Bible Familiarity: {fam['level']} - {fam['title']} - {fam['description']}")
