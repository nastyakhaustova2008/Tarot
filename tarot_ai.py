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


def generate_question_answer(question, card_name, meaning, orientation, lang="en"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"

    language_names = {"en": "English", "he": "Hebrew", "uk": "Ukrainian"}
    language_name = language_names.get(lang, "English")

    prompt_text = (
        f"You are a mystical tarot oracle. Respond in {language_name}.\n"
        f"User asked: '{question}'\n"
        f"Drawn Card: {card_name} ({orientation}) - Meaning: {meaning}\n"
        f"Provide a concise, insightful 3-4 sentence direct answer to their question using this card."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}}
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as error:
        print("GEMINI ERROR:", error)
        return None


def generate_two_person_prediction(name1, card1_name, card1_meaning, card1_orient,
                                   name2, card2_name, card2_meaning, card2_orient, lang="en"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"

    language_names = {"en": "English", "he": "Hebrew", "uk": "Ukrainian"}
    language_name = language_names.get(lang, "English")

    prompt_text = (
        f"You are a mystical tarot oracle. Respond in {language_name}.\n"
        f"Analyze the connection between two people:\n"
        f"1. {name1}: {card1_name} ({card1_orient}) - {card1_meaning}\n"
        f"2. {name2}: {card2_name} ({card2_orient}) - {card2_meaning}\n"
        f"Provide a 3-4 sentence reading describing their relationship dynamic and potential future."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 0}}
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as error:
        print("GEMINI ERROR:", error)
        return None