# Taro

A Flask web app for drawing tarot cards. Log in with your name, pull a card for your **Past**, **Present**, or **Future**, or draw a full three-card **Oracle** spread. Every reading is saved so you can look back at your history later.

The UI has a cyberpunk-forest theme: neon glow, scan lines, and glowing forest decorations layered over a dark background.

## Features

- **Session-based login** — enter a name and gender to start a session (no password required)
- **Four draw types** — Past, Present, Future, and Oracle (draws all three at once)
- **Card meanings** — each draw is pulled live from the [Tarot API](https://tarotapi.dev/), including upright/reversed orientation and its meaning
- **Card artwork** — card names are mapped to local image files for both Major and Minor Arcana
- **Reading history** — past readings are stored per user and category, with the last 30 per category kept
- **Themed UI** — matching login, main, and history pages styled around a dark, glowing forest aesthetic

## Tech stack

- **Backend:** Python, Flask
- **Database:** SQLite (`taro.db`)
- **External API:** [tarotapi.dev](https://tarotapi.dev/) for card names and meanings
- **Frontend:** Jinja2 templates, vanilla HTML/CSS

## Project structure

```
.
├── Tarot.py              # Flask app, routes, User/Card classes, error classes
├── Tarot_database.py     # SQLite connection, table creation, save/get/limit readings
├── templates/
│   ├── login.html        # Login page
│   ├── index.html        # Main page — draw cards
│   └── history.html      # Reading history page
└── static/
    └── ...                # Card images (Major/Minor Arcana artwork)
```

## How it works

1. **Login** (`/login`) — you submit your name and gender. The name can't be empty or purely numeric, and gender must be `man` or `woman`. This is stored in the Flask session — there's no password or account system.
2. **Draw a card** (`/draw/<category>`) — `category` is one of `past`, `present`, `future`, or `oracle`. The app calls the Tarot API for a random card (or three, for oracle), randomly assigns an upright/reversed orientation, and picks the matching meaning. The reading is saved to the database and shown on the page.
3. **View history** (`/history/<category>`) — pulls your past readings for that category (or all three for oracle) from the database and displays them.
4. **Logout** (`/logout`) — clears your session.

## Database

A single `readings` table stores every draw:

| Column       | Type    | Description                          |
|--------------|---------|---------------------------------------|
| `id`         | INTEGER | Primary key, auto-increment           |
| `user_name`  | TEXT    | Name entered at login                 |
| `category`   | TEXT    | `past`, `present`, or `future`        |
| `card_name`  | TEXT    | Name of the drawn card                |
| `meaning`    | TEXT    | Meaning text (upright or reversed)    |
| `orientation`| TEXT    | `upright` or `reversed`               |

Each user/category combination is capped at the 30 most recent readings — older ones are automatically deleted after a new draw.

## Setup

1. Install dependencies:
   ```bash
   pip install flask requests
   ```
2. Run the app:
   ```bash
   python Tarot.py
   ```
   This creates `taro.db` automatically on first run if it doesn't exist.
3. Open `http://localhost:5000` in your browser.

## Notes

- `app.secret_key` in `Tarot.py` is a placeholder — change it to a real random value before deploying anywhere outside local development.
- Card artwork filenames are derived from card names (e.g. `major_arcana_fool.png`, `minor_arcana_cups_ace.png`) and expected to live in the `static/` folder.
- If the Tarot API is unreachable, a `TarotAPIError` is raised — this currently isn't caught in the Flask routes, so it will surface as a server error until handled.
