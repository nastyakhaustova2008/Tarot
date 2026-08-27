import os
import base64
from urllib.parse import urlparse
from flask import Flask, render_template, session, redirect, request
from markupsafe import Markup, escape
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from mailer import send_reset_email
from card_model import Card
from tarot_ai import generate_question_answer, generate_two_person_prediction
import random
from datetime import datetime, timedelta
import re
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf import CSRFProtect

import database as Tarot_database
from exceptions import TarotAPIError
from user_model import User
from i18n import t, tr, tr_story, prefetch_translations, TRANSLATIONS
from tarot_ai import generate_oracle_story  # noqa: F401 (kept for parity with original imports)
from i18n import translate_meaning
from translations import MONTHS


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
csrf = CSRFProtect(app)

# ---------------------------------------------------------------
# Account / login-security settings
# ---------------------------------------------------------------
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = timedelta(hours=1)
RESET_TOKEN_LIFETIME_MINUTES = 60

Tarot_database.create_table()


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
app.jinja_env.globals["tr_story"] = tr_story


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
        login_error = session.pop("login_error", None)
        register_error = session.pop("register_error", None)
        show_register = session.pop("show_register", False)
        return render_template(
            "login.html",
            login_error=login_error,
            register_error=register_error,
            show_register=show_register,
        )

    card = session.get("last_card")
    category = session.get("last_category")
    story = session.get("last_story")

    oracle = None
    if session.get("last_oracle"):
        oracle = list(zip(session["last_oracle"], session["last_oracle_labels"]))

    # Warm the translation cache for everything this page needs, all at
    # once, instead of letting each card's name/meaning translate one
    # at a time as the template renders.
    texts_to_prefetch = []
    if card:
        texts_to_prefetch += [card["card_name"], card["meaning"]]
    if oracle:
        for oracle_card, _ in oracle:
            texts_to_prefetch += [oracle_card["card_name"], oracle_card["meaning"]]
    prefetch_translations(texts_to_prefetch)

    last_story_lang = session.get("last_story_lang", "en")
    current_lang = session.get("lang", "en")
    if story and current_lang != last_story_lang:
        prefetch_translations([story], lang=current_lang, assume_source_english=False)

    return render_template("home.html", card=card, category=category, oracle=oracle, story=story)


@app.route("/register", methods=["POST"])
def register():
    user_name = request.form["user_name"].strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    gender = request.form.get("gender")

    def fail(message):
        session["register_error"] = message
        session["show_register"] = True
        return redirect("/")

    if not user_name or user_name.isdigit():
        return fail(t("invalid_name"))
    if normalize_name(user_name) == MICHAEL_KOT_NORMALIZED:
        return fail(t("michael_kot_msg"))
    if gender != "man" and gender != "woman":
        return fail(t("invalid_gender"))
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return fail("Please enter a valid email address — it's needed to reset your password later.")
    if not password:
        return fail("Please enter a password.")
    if password != password_confirm:
        return fail("Passwords do not match. Please try again.")
    if len(password) < 4:
        return fail("Password must be at least 4 characters long.")

    if Tarot_database.get_user(user_name):
        return fail("Could not register with that username. Please choose another one or reset your password if it's yours.")

    password_hash = generate_password_hash(password)
    Tarot_database.create_user(user_name, password_hash, gender, email)

    session["user_name"] = user_name
    session["gender"] = gender
    return redirect("/")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        message = session.pop("forgot_message", None)
        return render_template("forgot_password.html", message=message)

    user_name = request.form.get("username", "").strip()

    # Always show the same message regardless of outcome, so we don't reveal
    # whether a given username exists in the system.
    generic_message = t("reset_link_sent_message")

    user_row = Tarot_database.get_user(user_name)
    if user_row:
        _, _, _, _, _, email = user_row
        if email:
            token = Tarot_database.create_reset_token(user_name, expires_minutes=RESET_TOKEN_LIFETIME_MINUTES)
            reset_link = get_base_url() + "/reset_password/" + token
            try:
                send_reset_email(email, reset_link)
            except Exception as error:
                # Don't expose email/SMTP failures to the visitor — log server-side instead.
                print("Failed to send password reset email:", error)

    session["forgot_message"] = generic_message
    return redirect("/forgot_password")


def get_base_url():
    codespace_name = os.environ.get("CODESPACE_NAME")
    if codespace_name:
        domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        return f"https://{codespace_name}-5000.{domain}"
    return request.host_url.rstrip("/")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_row = Tarot_database.get_reset_token(token)

    if not token_row:
        return render_template("reset_password.html", invalid=True)

    _, user_name, expires_at, used = token_row

    if used or datetime.now() > expires_at:
        return render_template("reset_password.html", invalid=True)

    if request.method == "GET":
        error = session.pop("reset_error", None)
        return render_template("reset_password.html", invalid=False, token=token, error=error)

    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not password or password != password_confirm:
        session["reset_error"] = "Passwords do not match. Please try again."
        return redirect(f"/reset_password/{token}")
    if len(password) < 4:
        session["reset_error"] = "Password must be at least 4 characters long."
        return redirect(f"/reset_password/{token}")

    new_hash = generate_password_hash(password)
    Tarot_database.update_password(user_name, new_hash)
    Tarot_database.mark_reset_token_used(token)

    session["login_error"] = "Your password has been reset. Please log in with your new password."
    return redirect("/")


@app.route("/login", methods=["POST"])
def login():
    user_name = request.form["user_name"].strip()
    password = request.form.get("password", "")

    if not user_name:
        session["login_error"] = t("invalid_name")
        return redirect("/")

    user_row = Tarot_database.get_user(user_name)
    if not user_row:
        session["login_error"] = "Incorrect username or password."
        return redirect("/")

    _, password_hash, gender, failed_attempts, locked_until, email = user_row

    # Still locked out?
    if locked_until and datetime.now() < locked_until:
        minutes_left = max(1, int((locked_until - datetime.now()).total_seconds() // 60) + 1)
        session["login_error"] = (
            f"Too many failed attempts. Try again in {minutes_left} minute(s), "
            f"or reset your password right away using the link below."
        )
        return redirect("/")

    # Lock period has expired -> treat as a fresh start generic_message
    if locked_until and datetime.now() >= locked_until:
        failed_attempts = 0

    if not check_password_hash(password_hash, password):
        failed_attempts += 1
        if failed_attempts >= MAX_LOGIN_ATTEMPTS:
            new_locked_until = datetime.now() + LOCKOUT_DURATION
            Tarot_database.record_failed_login(user_name, 0, new_locked_until)
            session["login_error"] = (
                "Incorrect password 3 times. This account is temporarily locked for 1 hour. "
                "You can reset your password right away using the link below instead of waiting."
            )
        else:
            Tarot_database.record_failed_login(user_name, failed_attempts, None)
            remaining = MAX_LOGIN_ATTEMPTS - failed_attempts
            session["login_error"] = f"Incorrect username or password. {remaining} attempt(s) remaining."
        return redirect("/")

    # Success — gender comes from the DB, never re-entered
    Tarot_database.reset_login_attempts(user_name)
    session["user_name"] = user_name
    session["gender"] = gender
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/draw/<category>", methods=["POST"])
def draw(category):
    if "user_name" not in session:
        return redirect("/")

    me = User(session["user_name"], session["gender"])

    try:
        if category == "past":
            me.get_past()
            card = me.past[-1]
            Tarot_database.save_reading_full(
                session["user_name"], "past", card.card_name, card.meaning, card.orientation,
                image_filename=card.image_filename
            )
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
            Tarot_database.save_reading_full(
                session["user_name"], "present", card.card_name, card.meaning, card.orientation,
                image_filename=card.image_filename
            )
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
            Tarot_database.save_reading_full(
                session["user_name"], "future", card.card_name, card.meaning, card.orientation,
                image_filename=card.image_filename
            )
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
            me.get_oracle(lang=session.get("lang", "en"))
            oracle = [
                (me.past[-1], "past"),
                (me.present[-1], "present"),
                (me.future[-1], "future"),
            ]

            gid = Tarot_database.new_group_id()
            for card, label in oracle:
                Tarot_database.save_reading_full(
                    session["user_name"], label, card.card_name, card.meaning, card.orientation,
                    group_id=gid, image_filename=card.image_filename
                )
            Tarot_database.save_oracle_story(
                session["user_name"], gid, me.oracle_story,
                response_lang=session.get("lang", "en")
            )

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
            session["last_story_lang"] = session.get("lang", "en")
            session["last_card"] = None
            session["last_category"] = None
            return redirect("/")

        else:
            return "Unknown category."

    except TarotAPIError as error:
        session["draw_error"] = str(error)
        return redirect("/")


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in TRANSLATIONS:
        session["lang"] = lang
    next_page = request.args.get("next") or request.referrer
    if next_page:
        parsed = urlparse(next_page)
        # Prevent open redirect vulnerabilities
        if not parsed.netloc and parsed.path.startswith("/"):
            return redirect(next_page)
    return redirect("/")


import base64
from flask import request, redirect, render_template, session

@app.route("/note/<int:reading_id>", methods=["GET", "POST"])
def note(reading_id):
    if "user_name" not in session:
        return redirect("/")
    user_name = session["user_name"]

    reading = Tarot_database.get_reading_by_id(reading_id, user_name)
    if not reading:
        return redirect("/")

    # Read the full 'next' parameter including query arguments (e.g. /history?category=two_person)
    next_url = request.args.get("next") or request.form.get("next") or f"/history?category={reading[1]}"

    if request.method == "POST":
        # Handle Cancel action
        if request.form.get("action") == "cancel":
            return redirect(next_url)

        note_text = request.form.get("note_text", "")[:6000]
        image_position_raw = request.form.get("image_position")
        image_position = int(image_position_raw) if image_position_raw else None

        # Safely extract existing note image
        note_image = reading[7] if len(reading) > 7 else None

        uploaded = request.files.get("note_image")
        if uploaded and uploaded.filename:
            ALLOWED_NOTE_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
            MAX_NOTE_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB

            if uploaded.mimetype not in ALLOWED_NOTE_IMAGE_TYPES:
                session["note_error"] = "Only PNG, JPEG, or WebP images are allowed."
                return redirect(next_url)

            image_bytes = uploaded.read(MAX_NOTE_IMAGE_BYTES + 1)
            if len(image_bytes) > MAX_NOTE_IMAGE_BYTES:
                session["note_error"] = "Image is too large (max 5 MB)."
                return redirect(next_url)

            note_image = "data:" + uploaded.mimetype + ";base64," + base64.b64encode(image_bytes).decode("utf-8")

        if request.form.get("remove_image") == "1":
            note_image = None
            image_position = None

        # Save note entry to database
        Tarot_database.save_note(reading_id, user_name, note_text, note_image, image_position)
        
        # Redirect back to the exact origin page
        return redirect(next_url)

    card_raw = reading[2] if len(reading) > 2 else None
    card_translated = tr(card_raw) if card_raw else None

    meta_info = {
        "category": reading[1] if len(reading) > 1 else "",
        "card_name": card_translated,
        "question": reading[9] if len(reading) > 9 else None,
        "target_name": reading[11] if len(reading) > 11 else None,
    }

    return render_template("note.html", reading=reading, meta_info=meta_info, next_url=next_url)
@app.route("/draw_yes_no", methods=["POST"])
def draw_yes_no():
    if "user_name" not in session:
        return redirect("/")

    question = request.form.get("question", "").strip()
    answer = "YES" if random.random() < 0.5 else "NO"

    Tarot_database.save_reading_full(
        session["user_name"],  # user_name
        "yes_no",              # category
        "Yes / No",            # card_name
        answer,                # meaning
        "upright",             # orientation
        None,                  # group_id
        question,              # question
        answer                 # ai_response
    )

    session["last_card"] = None
    session["last_oracle"] = None
    session["last_yes_no_result"] = {"question": question, "answer": answer}
    session["last_category"] = "yes_no"
    session["last_story"] = None

    return redirect("/")


@app.route("/ask_question", methods=["POST"])
def ask_question():
    if "user_name" not in session:
        return redirect("/")

    question = request.form.get("question", "").strip()
    lang = session.get("lang", "en")  # Get current language from session
    
    me = User(session["user_name"], session["gender"])
    me.get_present()
    card = me.present[-1]

    # Pass lang parameter
    ai_answer = generate_question_answer(question, card.card_name, card.meaning, card.orientation, lang=lang)

    Tarot_database.save_reading_full(
        session["user_name"],
        "question",
        card.card_name,
        card.meaning,
        card.orientation,
        question=question,
        ai_response=ai_answer,
        image_filename=card.image_filename,
        response_lang=lang

    )

    session["last_card"] = {
        "card_name": card.card_name,
        "meaning": card.meaning,
        "orientation": card.orientation,
        "image_filename": card.image_filename,
    }
    session["last_category"] = "question"
    session["last_oracle"] = None
    session["last_oracle_labels"] = None
    session["last_story"] = ai_answer
    session["last_story_lang"] = lang
    session["last_question_asked"] = question

    return redirect("/")


@app.route("/prediction_two", methods=["POST"])
def prediction_two():
    if "user_name" not in session:
        return redirect("/")

    name1 = request.form.get("name1", "").strip()
    name2 = request.form.get("name2", "").strip()
    lang = session.get("lang", "en")  # Get current language

    me = User(session["user_name"], session["gender"])
    me.get_oracle()
    card1, card2 = me.past[-1], me.present[-1]

    # Pass lang parameter
    ai_story = generate_two_person_prediction(
        name1, card1.card_name, card1.meaning, card1.orientation,
        name2, card2.card_name, card2.meaning, card2.orientation,
        lang=lang
    )

    gid = Tarot_database.new_group_id()

    Tarot_database.save_reading_full(
        session["user_name"], "two_person", card1.card_name, card1.meaning,
        card1.orientation, group_id=gid, question=f"{name1} & {name2}",
        ai_response=ai_story, target_name=name1, image_filename=card1.image_filename,
        response_lang=lang
    )
    Tarot_database.save_reading_full(
        session["user_name"], "two_person", card2.card_name, card2.meaning,
        card2.orientation, group_id=gid, question=f"{name1} & {name2}",
        ai_response=ai_story, target_name=name2, image_filename=card2.image_filename,
        response_lang=lang
    )

    session["last_oracle"] = [
        {"card_name": card1.card_name, "meaning": card1.meaning, "orientation": card1.orientation, "image_filename": card1.image_filename},
        {"card_name": card2.card_name, "meaning": card2.meaning, "orientation": card2.orientation, "image_filename": card2.image_filename},
    ]
    session["last_oracle_labels"] = [name1, name2]
    session["last_story"] = ai_story
    session["last_story_lang"] = lang
    session["last_card"] = None
    session["last_category"] = "prediction"
    session["last_question_asked"] = None

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

    if category == "two_person":
        groups = Tarot_database.get_two_person_groups(user_name)
        return render_template("history.html", category="two_person", gender=gender, two_person_groups=groups)

    if category not in ("past", "present", "future", "yes_no", "question"):
        return "Unknown category."

    rows = Tarot_database.get_readings(user_name, category)
    return render_template("history.html", category=category, gender=gender, rows=rows)


@app.route('/calendar')
def calendar_view():
    user_name = session.get('user_name')
    current_lang = session.get('lang', 'en')

    raw_calendar_data = Tarot_database.get_calendar_data(user_name, current_lang)

    month_param = request.args.get('month', '')
    if re.match(r'^\d{4}-\d{2}$', month_param):
        selected_key = month_param
    elif raw_calendar_data:
        selected_key = max(raw_calendar_data.keys())
    else:
        selected_key = datetime.now().strftime('%Y-%m')

    year, month = (int(part) for part in selected_key.split('-'))

    month_entry = raw_calendar_data.get(selected_key)
    days = month_entry['days'] if month_entry else {}

    if days:
        for day_num, predictions in days.items():
            if not isinstance(predictions, list):
                continue
            for pred in predictions:
                if not isinstance(pred, dict):
                    continue
                # ai_response was generated in whatever language was active
                # at the time — never assume it's already English.
                response_lang = pred.get('response_lang') or 'en'
                if pred.get('ai_response') and isinstance(pred['ai_response'], str) and response_lang != current_lang:
                    pred['ai_response'] = translate_meaning(pred['ai_response'], current_lang, assume_source_english=False)
                if current_lang != 'en' and pred.get('question') and isinstance(pred['question'], str):
                    pred['question'] = translate_meaning(pred['question'], current_lang)
                cards = pred.get('cards')
                if isinstance(cards, list):
                    for card in cards:
                        # Card meanings always come from tarotapi.dev in
                        # English, so the "en" shortcut is correct here.
                        if isinstance(card, dict) and card.get('meaning') and isinstance(card['meaning'], str) and current_lang != 'en':
                            card['meaning'] = translate_meaning(card['meaning'], current_lang)

    months_table = MONTHS.get(current_lang, MONTHS['en'])
    month_label = f"{months_table.get(month, month)} {year}"

    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    next_year, next_month = (year, month + 1) if month < 12 else (year + 1, 1)

    before_first_prediction = bool(raw_calendar_data) and selected_key < min(raw_calendar_data.keys())
    return render_template(
        'calendar.html',
        days=days,
        month_label=month_label,
        prev_month=f"{prev_year:04d}-{prev_month:02d}",
        next_month=f"{next_year:04d}-{next_month:02d}",
        before_first_prediction=before_first_prediction,

    )

from flask import request, render_template, session

@app.route('/history')
def history_view():
    category = request.args.get('category', 'past')
    user_name = session.get('user_name')
    
    # Query database according to selected category
    if category == 'oracle':
        groups = Tarot_database.get_oracle_groups(user_name)
        return render_template('history.html', category=category, groups=groups)
    elif category == 'two_person':
        two_person_groups = Tarot_database.get_two_person_groups(user_name)
        return render_template('history.html', category=category, two_person_groups=two_person_groups)
    else:
        rows = Tarot_database.get_readings(user_name, category)
        return render_template('history.html', category=category, rows=rows)


if __name__ == "__main__":
    Tarot_database.create_table()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




