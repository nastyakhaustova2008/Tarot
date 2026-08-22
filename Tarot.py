import requests
import random
import Tarot_database
from flask import Flask, render_template, session, redirect, request


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
            print(card.give_card())

    def get_oracle(self):
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()                 #print(data)
            card_data1 = data["cards"][0]
            card_name1 = card_data1["name"]
            random_meaning1 = random.choice(["upright", "reversed"])
            if random_meaning1 == "upright":
                meaning1 = card_data1["meaning_up"]
            else:
                meaning1 = card_data1["meaning_rev"]
            card1 = Card(card_name1, meaning1, random_meaning1)
            print(card1.card_name, "->", card1.image_filename)
            self.past.append(card1)
            Tarot_database.save_reading(self.user_name, "past", card1.card_name, card1.meaning, card1.orientation)
            print(card1.give_card())

            card_data2 = data["cards"][1]
            card_name2 = card_data2["name"]
            random_meaning2 = random.choice(["upright", "reversed"])
            if random_meaning2 == "upright":
                meaning2 = card_data2["meaning_up"]
            else:
                meaning2 = card_data2["meaning_rev"]
            card2 = Card(card_name2, meaning2, random_meaning2)
            print(card2.card_name, "->", card2.image_filename)
            self.present.append(card2)
            Tarot_database.save_reading(self.user_name, "present", card2.card_name, card2.meaning, card2.orientation)
            print(card2.give_card())

            card_data3 = data["cards"][2]
            card_name3 = card_data3["name"]
            random_meaning3 = random.choice(["upright", "reversed"])
            if random_meaning3 == "upright":
                meaning3 = card_data3["meaning_up"]
            else:
                meaning3 = card_data3["meaning_rev"]
            card3 = Card(card_name3, meaning3, random_meaning3)
            print(card3.card_name, "->", card3.image_filename)
            self.future.append(card3)
            Tarot_database.save_reading(self.user_name, "future", card3.card_name, card3.meaning, card3.orientation)
            print(card3.give_card())


app = Flask(__name__)
app.secret_key = "change_this_to_something_random"

@app.route("/")
def home():
    if "user_name" not in session:
        return render_template("login.html")
    return render_template("index.html", card=None)

@app.route("/login", methods=["POST"])
def login():
    user_name = request.form["user_name"]
    gender = request.form["gender"]

    if user_name.isdigit() or not user_name:
        return "Invalid name, go back and try again."
    if gender != "man" and gender != "woman":
        return "Invalid gender, go back and try again."

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

    if category == "past":
        me.get_past()
        return render_template("index.html", card=me.past[-1], category="Past")
    elif category == "present":
        me.get_present()
        return render_template("index.html", card=me.present[-1], category="Present")
    elif category == "future":
        me.get_future()
        return render_template("index.html", card=me.future[-1], category="Future")
    elif category == "oracle":
        me.get_oracle()
        oracle = [
            (me.past[-1], "Past"),
            (me.present[-1], "Present"),
            (me.future[-1], "Future"),
        ]
        return render_template("index.html", oracle=oracle)
    else:
        return "Unknown category."

@app.route("/history/<category>")
def history(category):
    if "user_name" not in session:
        return redirect("/")

    user_name = session["user_name"]
    gender = session["gender"]

    if category == "oracle":
        past_rows = Tarot_database.get_readings(user_name, "past")
        present_rows = Tarot_database.get_readings(user_name, "present")
        future_rows = Tarot_database.get_readings(user_name, "future")
        return render_template("history.html", category="oracle", gender=gender,
                                past_rows=past_rows, present_rows=present_rows, future_rows=future_rows)

    if category not in ("past", "present", "future"):
        return "Unknown category."

    rows = Tarot_database.get_readings(user_name, category)
    return render_template("history.html", category=category, gender=gender, rows=rows)

if __name__ == "__main__":
    Tarot_database.create_table()
    app.run(debug=True)

