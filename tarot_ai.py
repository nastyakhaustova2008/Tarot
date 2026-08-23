from dotenv import load_dotenv
import os
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def generate_oracle_story(past_meaning, present_meaning, future_meaning, lang="en"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"

    language_names = {
        "en": "English",
        "he": "Hebrew",
        "uk": "Ukrainian",
    }
    language_name = language_names.get(lang, "English")

    prompt_text = (
        f"You are a mystical fortune teller. Write your entire response in {language_name}. "
        f"Write a short, flowing 3-sentence story weaving together these three tarot meanings: "
        f"Past - {past_meaning}. "
        f"Present - {present_meaning}. "
        f"Future - {future_meaning}."
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt_text}]}
        ],
        "generationConfig": {
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        print("GEMINI RAW RESPONSE:", data)  # temporary debug line
        story = data["candidates"][0]["content"]["parts"][0]["text"]
        return story
    except (requests.exceptions.RequestException, KeyError) as error:
        print("GEMINI ERROR:", error)  # temporary debug line
        return None