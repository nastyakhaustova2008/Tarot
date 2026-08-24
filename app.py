import os
import base64
from urllib.parse import urlparse
from flask import Flask, render_template, session, redirect, request
from markupsafe import Markup, escape
from dotenv import load_dotenv

import database as Tarot_database
from exceptions import TarotAPIError
from user_model import User
from i18n import t, tr, TRANSLATIONS
from tarot_ai import generate_oracle_story  # noqa: F401 (kept for parity with original imports)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = "change_this_to_something_random"


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
app.jinja_env.globals["t"] = t
app.jinja_env.globals["tr"] = tr


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


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in TRANSLATIONS:
        session["lang"] = lang
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/"):
        return redirect(next_page)
    return redirect("/")


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