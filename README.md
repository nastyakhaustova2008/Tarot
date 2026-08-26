# Taro

A Flask web app for tarot readings. Register an account, pull a card for your **Past**, **Present**, or **Future**, draw a full three-card **Oracle** spread, ask a yes/no question, or ask the oracle a free-form question and get an AI-generated answer. Every reading is saved so you can revisit it later in your history or on a monthly calendar view.

The UI has a cyberpunk-forest theme: neon glow, scan lines, and glowing forest decorations layered over a dark background, with English, Hebrew, and Ukrainian language support.

## Features

- **Accounts with password auth** — register with a name, email, gender, and password; passwords are hashed with Werkzeug, and failed logins are rate-limited (account locks for 1 hour after 3 wrong attempts)
- **Password reset by email** — "forgot password" flow emails a time-limited reset link via SMTP
- **Five reading types**
  - **Past / Present / Future** — single-card draws
  - **Oracle** — all three cards at once, plus a short AI-generated story weaving them together
  - **Yes/No** — a quick coin-flip style answer to a typed question
  - **Ask a question** — draws a present card and asks the AI to answer your question through it
  - **Two-person prediction** — an AI-generated reading linking two named people to a pair of drawn cards
- **Card meanings** — pulled live from the [Tarot API](https://tarotapi.dev/), including upright/reversed orientation
- **AI storytelling** — oracle stories, question answers, and two-person predictions are generated with Google's Gemini API, in the user's selected language
- **Card artwork** — card names are mapped to local image files for both Major and Minor Arcana
- **Reading history** — past readings are stored per user and category (last 30 per category kept), viewable as a list or grouped by oracle/two-person session
- **Calendar view** — browse past readings by month
- **Notes on readings** — attach a text note and/or an inline image to any saved reading
- **Multi-language UI** — English, Hebrew, and Ukrainian, with on-the-fly translation (and caching) of AI-generated text via `deep-translator`

## Tech stack

- **Backend:** Python, Flask
- **Database:** PostgreSQL (via `psycopg2`)
- **External APIs:**
  - [tarotapi.dev](https://tarotapi.dev/) for card names and meanings
  - Google Gemini API for AI-generated stories/answers
  - Google Translate (via `deep-translator`) for UI/content translation
- **Frontend:** Jinja2 templates, vanilla HTML/CSS
- **Email:** SMTP (Gmail) for password reset links

## Project structure

```
.
├── app.py                 # Flask app and all routes
├── user_model.py          # User class — fetches/draws cards per user
├── card_model.py           # Card class + card-name → image filename mapping
├── database.py             # PostgreSQL connection, schema, reading/user queries
├── exceptions.py           # Custom exceptions (TarotAPIError, etc.)
├── tarot_ai.py              # Gemini-powered story/answer/prediction generation
├── i18n.py                  # Translation helpers (t(), tr(), translate_meaning())
├── translations.py          # Static translation strings, month names
├── mailer.py                 # Password-reset email sending (SMTP)
├── check_email_env.py         # Small script to debug EMAIL_* env vars
├── test_db.py                  # Ad-hoc DB test script
├── templates/
│   ├── base.html              # Shared layout
│   ├── login.html             # Login / register page
│   ├── home.html               # Main page — draw cards, ask questions
│   ├── history.html             # Reading history page
│   ├── calendar.html             # Monthly calendar of readings
│   ├── note.html                  # Add/edit a note on a reading
│   ├── forgot_password.html        # Request a password reset
│   ├── reset_password.html          # Set a new password
│   └── partials/                     # Shared includes (nav, decorations, macros, etc.)
└── static/
    └── ...                    # Card artwork (Major/Minor Arcana)
```

> The `history/` folder in this repo holds an earlier, standalone version of the app (`Tarot.py`, `Tarot_database.py`, SQLite-based) kept for reference — it is not part of the current app.

## How it works

1. **Register** (`/register`) — submit a name, gender, email, and password. Email is required (used for password reset) and passwords are hashed before storage.
2. **Login** (`/login`) — name + password. Failed attempts are tracked; 3 in a row locks the account for an hour (a reset link is offered instead of waiting).
3. **Forgot / reset password** (`/forgot_password`, `/reset_password/<token>`) — emails a reset link valid for 60 minutes.
4. **Draw a card** (`/draw/<category>`, POST) — `category` is one of `past`, `present`, `future`, or `oracle`. The app calls the Tarot API for a random card (or three, for oracle), randomly assigns an upright/reversed orientation, and picks the matching meaning. For oracle draws, it also generates an AI story linking the three cards.
5. **Yes/No** (`/draw_yes_no`, POST) — flips a coin for a typed question, no card involved.
6. **Ask a question** (`/ask_question`, POST) — draws a present card and asks Gemini to answer the question through that card.
7. **Two-person prediction** (`/prediction_two`, POST) — draws two cards and asks Gemini for a reading connecting two named people.
8. **View history** (`/history/<category>` or `/history?category=...`) — past readings for a category, or grouped oracle/two-person sessions.
9. **Calendar** (`/calendar`) — readings grouped by month, translated on the fly if the UI language isn't English.
10. **Notes** (`/note/<reading_id>`) — attach text and/or an inline image to a saved reading.
11. **Language switch** (`/set_language/<lang>`) — switches the UI language (`en`, `he`, `uk`) for the session.
12. **Logout** (`/logout`) — clears the session.

## Database

Backed by PostgreSQL. Key tables (managed automatically by `database.create_table()`):

- **`readings`** — every draw, one row per card. Columns include `user_name`, `category`, `card_name`, `meaning`, `orientation`, `group_id` (links multi-card draws like oracle/two-person), `question`, `ai_response`, `target_name`, `image_filename`, `note_text`, `note_image`, `note_image_position`, and `created_at`.
- **`oracle_stories`** — the AI-generated story text for each oracle draw, linked by `group_id`.
- **`users`** — account records (name, password hash, gender, email, failed-login tracking).
- **Password reset tokens** and a **translation cache** table are also created/managed here.

Each user/category combination keeps only the 30 most recent readings — older ones are pruned automatically.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Create a `.env` file** in the project root with:
   ```
   DATABASE_URL=postgresql://user:password@host:port/dbname
   GEMINI_API_KEY=your_gemini_api_key
   EMAIL_ADDRESS=your_gmail_address
   EMAIL_APP_PASSWORD=your_gmail_app_password
   ```
   - `DATABASE_URL` — required; a PostgreSQL connection string.
   - `GEMINI_API_KEY` — required for oracle stories, question answers, and two-person predictions.
   - `EMAIL_ADDRESS` / `EMAIL_APP_PASSWORD` — required for the "forgot password" email flow (a Gmail address + [app password](https://support.google.com/accounts/answer/185833)).
3. **Run the app:**
   ```bash
   python app.py
   ```
   This creates/updates the necessary tables automatically on startup.
4. Open `http://localhost:5000` in your browser.

The included `Procfile` (`web: python app.py`) is set up for deployment on platforms like Heroku.

## Notes

- `app.secret_key` in `app.py` is a placeholder — change it to a real random value before deploying anywhere outside local development.
- Card artwork filenames are derived from card names (e.g. `major_arcana_fool.png`, `minor_arcana_cups_ace.png`) and expected to live in the `static/` folder.
- If the Tarot API is unreachable, a `TarotAPIError` is raised and shown to the user as a "server is not responding" message.
- If `GEMINI_API_KEY` isn't set or the Gemini API call fails, AI-generated text (stories/answers) will be `None` rather than raising an error.
- If email isn't configured, password-reset requests still succeed silently (no email is sent) — this is intentional so the app doesn't reveal whether a username exists.