import requests
import random
import Tarot_database
from flask import Flask, render_template, session, redirect, request
import os
from translations import TRANSLATIONS
from deep_translator import MyMemoryTranslator
from dotenv import load_dotenv
from tarot_ai import generate_oracle_story
from markupsafe import Markup, escape


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class WrongNameError(Exception):
    def __init__(self, user_name):
        self.user_name = user_name

    def __str__(self):
        return f"You wrote name {self.user_name} it is wrong, name shouldn't be numbers"


class WrongGenderError(Exception):
    def __init__(self, gender):
        self.gender = gender

    def __str__(self):
        return f"You wrote {self.gender} it is wrong, gender can be man or woman"


class WrongDigitError(Exception):
    def __init__(self, do_next):
        self.do_next = do_next

    def __str__(self):
        return f"You wrote {self.do_next}, but you can choose only '1', '2', '3', '4', '5', '6', '7', '8' or '9'."
        

class TarotAPIError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return f"Server is not responding, try agein later"


MAJOR_ARCANA_FILES = {
    "The Fool": "major_arcana_fool.png",
    "The Magician": "major_arcana_magician.png",
    "The High Priestess": "major_arcana_priestess.png",
    "The Empress": "major_arcana_empress.png",
    "The Emperor": "major_arcana_emperor.png",
    "The Hierophant": "major_arcana_hierophant.png",
    "The Lovers": "major_arcana_lovers.png",
    "The Chariot": "major_arcana_chariot.png",
    "Strength": "major_arcana_strength.png",
    "The Hermit": "major_arcana_hermit.png",
    "Wheel of Fortune": "major_arcana_fortune.png",
    "Justice": "major_arcana_justice.png",
    "The Hanged Man": "major_arcana_hanged.png",
    "Death": "major_arcana_death.png",
    "Temperance": "major_arcana_temperance.png",
    "The Devil": "major_arcana_devil.png",
    "The Tower": "major_arcana_tower.png",
    "The Star": "major_arcana_star.png",
    "The Moon": "major_arcana_moon.png",
    "The Sun": "major_arcana_sun.png",
    "Judgement": "major_arcana_judgement.png",
    "The World": "major_arcana_world.png",
}

MAJOR_ARCANA_ALIASES = {
    "the last judgment": "major_arcana_judgement.png",
    "judgment": "major_arcana_judgement.png",
    "fortitude": "major_arcana_strength.png",
}

RANK_TO_CODE = {
    "Ace": "ace", "Two": "2", "Three": "3", "Four": "4", "Five": "5",
    "Six": "6", "Seven": "7", "Eight": "8", "Nine": "9", "Ten": "10",
    "Page": "page", "Knight": "knight", "Queen": "queen", "King": "king",
}


def get_image_filename(card_name):
    normalized_majors = {name.lower(): filename for name, filename in MAJOR_ARCANA_FILES.items()}
    name_lower = card_name.lower()

    if name_lower in normalized_majors:
        return normalized_majors[name_lower]

    if name_lower in MAJOR_ARCANA_ALIASES:
        return MAJOR_ARCANA_ALIASES[name_lower]

    parts = card_name.split(" of ")
    if len(parts) != 2:
        parts = card_name.lower().split(" of ")

    if len(parts) == 2:
        rank, suit = parts
        rank_code = RANK_TO_CODE.get(rank.title(), rank.lower())
        suit_code = suit.lower()
        return f"minor_arcana_{suit_code}_{rank_code}.png"

    return None

    
class Card():
    def __init__(self, card_name, meaning, random_meaning):
        self.card_name = card_name
        self.meaning = meaning
        self.orientation = random_meaning
        self.image_filename = get_image_filename(card_name)

    def give_card(self):
        return f"You've got {self.card_name} it means: {self.meaning}"

    def give_meaning(self):
        return f"{self.meaning}"


class User():
    def __init__(self, user_name, gender):
        self.user_name = user_name
        self.gender = gender
        self.past = []
        self.present = [] 
        self.future = []

    def my_past(self):
        if self.gender == "man":
            print(f"Sir {self.user_name}, previousli you got on your past:")
        else:
            print(f"Ledy {self.user_name}, previousli you got on your present:")
        count_up = 0
        count_rev = 0
        rows = Tarot_database.get_readings(self.user_name, "past")
        Tarot_database.limit_readings(self.user_name, "past", 30)
        for _, meaning, orientation in rows:
            print(meaning)
            if orientation == "upright":
                count_up += 1
            else:
                count_rev += 1
        print(f"In the end you got {count_up} upright cards and {count_rev} reversed cards")

    def my_present(self):
        if self.gender == "man":
            print(f"Sir {self.user_name}, previousli you got on your past:")
        else:
            print(f"Ledy {self.user_name}, previousli you got on your present:")
        count_up = 0
        count_rev = 0
        rows = Tarot_database.get_readings(self.user_name, "present")
        Tarot_database.limit_readings(self.user_name, "present", 30)
        for _, meaning, orientation in rows:
            print(meaning)
            if orientation == "upright":
                count_up += 1
            else:
                count_rev += 1
        print(f"In the end you got {count_up} upright cards and {count_rev} reversed cards")

    def my_future(self):
            if self.gender == "man":
                print(f"Sir {self.user_name}, previousli you got on your future:")
            else:
                print(f"Ledy {self.user_name}, previousli you got on your future:")
            count_up = 0
            count_rev = 0
            rows = Tarot_database.get_readings(self.user_name, "future")
            Tarot_database.limit_readings(self.user_name, "future", 30)
            for _, meaning, orientation in rows:
                print(meaning)
                if orientation == "upright":
                    count_up += 1
                else:
                    count_rev += 1
            print(f"In the end you got {count_up} upright cards and {count_rev} reversed cards")

    def my_oracle(self):
            if self.gender == "man":
                print(f"Sir {self.user_name}, previousli you got:")
            else:
                print(f"Ledy {self.user_name}, previousli you got:")
            count_up1 = 0
            count_rev1 = 0
            print("Oracles about past:")
            rows = Tarot_database.get_readings(self.user_name, "past")
            Tarot_database.limit_readings(self.user_name, "past", 30)
            for _, meaning, orientation in rows:
                print(meaning)
                if orientation == "upright":
                    count_up1 += 1
                else:
                    count_rev1 += 1
            print(f"In the end you got {count_up1} upright cards and {count_rev1} reversed cards")

            count_up2 = 0
            count_rev2 = 0
            print("Oracles about present:")
            rows = Tarot_database.get_readings(self.user_name, "present")
            Tarot_database.limit_readings(self.user_name, "present", 30)
            for _, meaning, orientation in rows:
                print(meaning)
                if orientation == "upright":
                    count_up2 += 1
                else:
                    count_rev2 += 1
            print(f"In the end you got {count_up2} upright cards and {count_rev2} reversed cards")

            count_up3 = 0
            count_rev3 = 0
            print("Oracles about future:")
            rows = Tarot_database.get_readings(self.user_name, "future")
            Tarot_database.limit_readings(self.user_name, "future", 30)
            for _, meaning, orientation in rows:
                print(meaning)
                if orientation == "upright":
                    count_up3 += 1
                else:
                    count_rev3 += 1
            print(f"In the end you got {count_up3} upright cards and {count_rev3} reversed cards")

    def get_past(self):
            try:
                response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
            except requests.exceptions.RequestException:
                raise TarotAPIError()
            else:
                data = response.json()                 #print(data)
                card_data = data["cards"][0]
                card_name = card_data["name"]
                random_meaning = random.choice(["upright", "reversed"])
                if random_meaning == "upright":
                    meaning = card_data["meaning_up"]
                else:
                    meaning = card_data["meaning_rev"]
                card = Card(card_name, meaning, random_meaning)
                self.past.append(card)
                Tarot_database.save_reading(self.user_name, "past", card.card_name, card.meaning, card.orientation)
                Tarot_database.limit_readings(self.user_name, "past", 30)
                print(card.give_card())

    def get_present(self):
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()                 #print(data)
            card_data = data["cards"][0]
            card_name = card_data["name"]
            random_meaning = random.choice(["upright", "reversed"])
            if random_meaning == "upright":
                meaning = card_data["meaning_up"]
            else:
                meaning = card_data["meaning_rev"]
            card = Card(card_name, meaning, random_meaning)
            self.present.append(card)
            Tarot_database.save_reading(self.user_name, "present", card.card_name, card.meaning, card.orientation)
            Tarot_database.limit_readings(self.user_name, "present", 30)
            print(card.give_card())

    def get_future(self):
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()                 #print(data)
            card_data = data["cards"][0]
            card_name = card_data["name"]
            random_meaning = random.choice(["upright", "reversed"])
            if random_meaning == "upright":
                meaning = card_data["meaning_up"]
            else:
                meaning = card_data["meaning_rev"]
            card = Card(card_name, meaning, random_meaning)
            self.future.append(card)
            Tarot_database.save_reading(self.user_name, "future", card.card_name, card.meaning, card.orientation)
            Tarot_database.limit_readings(self.user_name, "future", 30)
            print(card.give_card())

    def get_oracle(self):
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()
            group_id = Tarot_database.new_group_id()

            card_data1 = data["cards"][0]
            card_name1 = card_data1["name"]
            random_meaning1 = random.choice(["upright", "reversed"])
            meaning1 = card_data1["meaning_up"] if random_meaning1 == "upright" else card_data1["meaning_rev"]
            card1 = Card(card_name1, meaning1, random_meaning1)
            self.past.append(card1)
            Tarot_database.save_reading(self.user_name, "past", card1.card_name, card1.meaning, card1.orientation, group_id)
            Tarot_database.limit_readings(self.user_name, "past", 30)

            card_data2 = data["cards"][1]
            card_name2 = card_data2["name"]
            random_meaning2 = random.choice(["upright", "reversed"])
            meaning2 = card_data2["meaning_up"] if random_meaning2 == "upright" else card_data2["meaning_rev"]
            card2 = Card(card_name2, meaning2, random_meaning2)
            self.present.append(card2)
            Tarot_database.save_reading(self.user_name, "present", card2.card_name, card2.meaning, card2.orientation, group_id)
            Tarot_database.limit_readings(self.user_name, "present", 30)

            card_data3 = data["cards"][2]
            card_name3 = card_data3["name"]
            random_meaning3 = random.choice(["upright", "reversed"])
            meaning3 = card_data3["meaning_up"] if random_meaning3 == "upright" else card_data3["meaning_rev"]
            card3 = Card(card_name3, meaning3, random_meaning3)
            self.future.append(card3)
            Tarot_database.save_reading(self.user_name, "future", card3.card_name, card3.meaning, card3.orientation, group_id)
            Tarot_database.limit_readings(self.user_name, "future", 30)

            story = generate_oracle_story(meaning1, meaning2, meaning3, lang="en")
            Tarot_database.save_oracle_story(self.user_name, group_id, story)

            self.last_group_id = group_id
            self.oracle_story = story


app = Flask(__name__)


def render_note(note_text, note_image, image_position):
    if not note_text and not note_image:
        return ""
    text = note_text or ""
    if note_image and image_position is not None and 0 <= image_position <= len(text):
        before = escape(text[:image_position])
        after = escape(text[image_position:])
        img_tag = Markup(f'<img src="{note_image}" class="note-inline-img" alt="note">')
        return Markup(before) + img_tag + Markup(after)
    elif note_image:
        return Markup(escape(text)) + Markup(f'<img src="{note_image}" class="note-inline-img" alt="note">')
    else:
        return Markup(escape(text))

app.jinja_env.globals["render_note"] = render_note


def t(key):
    lang = session.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

app.jinja_env.globals["t"] = t

LANG_CODE_MAP = {"en": "en-US", "he": "he-IL", "uk": "uk-UA"}

_translation_cache = {}

def translate_meaning(text, lang):
    if lang == "en":
        return text

    cached = Tarot_database.get_cached_translation(text, lang)
    if cached:
        return cached

    try:
        target = LANG_CODE_MAP.get(lang, lang)
        translated = MyMemoryTranslator(source="en-US", target=target, email="nastyakhaustova2008@gmail.com").translate(text)

        if not translated or "Error 500" in translated or "Server Error" in translated or len(translated) > len(text) * 4:
            print("TRANSLATE REJECTED RESULT:", translated, flush=True)
            return text

        Tarot_database.save_cached_translation(text, lang, translated)
        return translated
    except Exception as error:
        print("TRANSLATE FAILED:", repr(error), flush=True)
        return text
    

def tr(text):
    return translate_meaning(text, session.get("lang", "en"))

app.jinja_env.globals["tr"] = tr


app.secret_key = "change_this_to_something_random"


@app.route("/")
def home():
    if "user_name" not in session:
        error = session.pop("login_error", None)
        return render_template("login.html", error=error)

    card = session.get("last_card")
    category = session.get("last_category")
    story = session.get("last_story")

    oracle = None
    if session.get("last_oracle"):
        oracle = list(zip(session["last_oracle"], session["last_oracle_labels"]))

    return render_template("index.html", card=card, category=category, oracle=oracle, story=story)


HOMOGLYPH_MAP = {
    "а": "a", "е": "e", "о": "o", "с": "c", "р": "p",
    "х": "x", "у": "y", "к": "k", "м": "m", "н": "h",
    "т": "t", "і": "i", "ѕ": "s", "ј": "j",
}

def normalize_name(name):
    name = name.strip().lower()
    normalized = "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in name)
    words = normalized.split()
    return " ".join(sorted(words))

MICHAEL_KOT_NORMALIZED = normalize_name("Michael Kot")


@app.route("/login", methods=["POST"])
def login():
    user_name = request.form["user_name"].strip()
    gender = request.form["gender"]

    if not user_name or user_name.isdigit():
        session["login_error"] = t("invalid_name")
        return redirect("/")
    if normalize_name(user_name) == MICHAEL_KOT_NORMALIZED:
        session["login_error"] = t("michael_kot_msg")
        return redirect("/")
    if gender != "man" and gender != "woman":
        session["login_error"] = t("invalid_gender")
        return redirect("/")

    session["user_name"] = user_name
    session["gender"] = gender
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/draw/<category>")
def draw(category):
    if "user_name" not in session:
        return redirect("/")

    me = User(session["user_name"], session["gender"])

    try:
        if category == "past":
            me.get_past()
            card = me.past[-1]
            session["last_card"] = {
                "card_name": card.card_name,
                "meaning": card.meaning,
                "orientation": card.orientation,
                "image_filename": card.image_filename,
            }
            session["last_category"] = "past"
            session["last_oracle"] = None
            session["last_story"] = None
            return redirect("/")

        elif category == "present":
            me.get_present()
            card = me.present[-1]
            session["last_card"] = {
                "card_name": card.card_name,
                "meaning": card.meaning,
                "orientation": card.orientation,
                "image_filename": card.image_filename,
            }
            session["last_category"] = "present"
            session["last_oracle"] = None
            session["last_story"] = None
            return redirect("/")

        elif category == "future":
            me.get_future()
            card = me.future[-1]
            session["last_card"] = {
                "card_name": card.card_name,
                "meaning": card.meaning,
                "orientation": card.orientation,
                "image_filename": card.image_filename,
            }
            session["last_category"] = "future"
            session["last_oracle"] = None
            session["last_story"] = None
            return redirect("/")

        elif category == "oracle":
            me.get_oracle()
            oracle = [
                (me.past[-1], "past"),
                (me.present[-1], "present"),
                (me.future[-1], "future"),
            ]
            session["last_oracle"] = [
                {
                    "card_name": card.card_name,
                    "meaning": card.meaning,
                    "orientation": card.orientation,
                    "image_filename": card.image_filename,
                }
                for card, label in oracle
            ]
            session["last_oracle_labels"] = [label for card, label in oracle]
            session["last_story"] = me.oracle_story
            session["last_card"] = None
            session["last_category"] = None
            return redirect("/")

        else:
            return "Unknown category."

    except TarotAPIError as error:
        session["draw_error"] = str(error)
        return redirect("/")

@app.route("/history/<category>")
def history(category):
    if "user_name" not in session:
        return redirect("/")

    user_name = session["user_name"]
    gender = session["gender"]

    if category == "oracle":
        groups = Tarot_database.get_oracle_groups(user_name)
        return render_template("history.html", category="oracle", gender=gender, groups=groups)

    if category not in ("past", "present", "future"):
        return "Unknown category."

    rows = Tarot_database.get_readings(user_name, category)
    return render_template("history.html", category=category, gender=gender, rows=rows)
    

from urllib.parse import urlparse

@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in TRANSLATIONS:
        session["lang"] = lang
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/"):
        return redirect(next_page)
    return redirect("/")


import base64

@app.route("/note/<int:reading_id>", methods=["GET", "POST"])
def note(reading_id):
    if "user_name" not in session:
        return redirect("/")
    user_name = session["user_name"]

    reading = Tarot_database.get_reading_by_id(reading_id, user_name)
    if not reading:
        return redirect("/")

    if request.method == "POST":
        note_text = request.form.get("note_text", "")[:6000]
        image_position_raw = request.form.get("image_position")
        image_position = int(image_position_raw) if image_position_raw else None

        note_image = reading[7]  # keep existing image by default

        uploaded = request.files.get("note_image")
        if uploaded and uploaded.filename:
            note_image = "data:" + uploaded.mimetype + ";base64," + base64.b64encode(uploaded.read()).decode("utf-8")

        if request.form.get("remove_image") == "1":
            note_image = None
            image_position = None

        Tarot_database.save_note(reading_id, user_name, note_text, note_image, image_position)
        return redirect(f"/history/{reading[1]}")

    return render_template("note.html", reading=reading)


if __name__ == "__main__":
    Tarot_database.create_table()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

