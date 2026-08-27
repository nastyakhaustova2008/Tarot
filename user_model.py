import requests
import random
import database as Tarot_database
from card_model import Card
from exceptions import TarotAPIError
from tarot_ai import generate_oracle_story


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
        """Fetches a random card for 'past'. Does NOT save to the database —
        app.py's /draw route is responsible for saving, so it's only saved once."""
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()
            card_data = data["cards"][0]
            card_name = card_data["name"]
            random_meaning = random.choice(["upright", "reversed"])
            if random_meaning == "upright":
                meaning = card_data["meaning_up"]
            else:
                meaning = card_data["meaning_rev"]
            card = Card(card_name, meaning, random_meaning)
            self.past.append(card)
            print(card.give_card())

    def get_present(self):
        """Fetches a random card for 'present'. Does NOT save to the database —
        app.py's /draw route is responsible for saving, so it's only saved once."""
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()
            card_data = data["cards"][0]
            card_name = card_data["name"]
            random_meaning = random.choice(["upright", "reversed"])
            if random_meaning == "upright":
                meaning = card_data["meaning_up"]
            else:
                meaning = card_data["meaning_rev"]
            card = Card(card_name, meaning, random_meaning)
            self.present.append(card)
            print(card.give_card())

    def get_future(self):
        """Fetches a random card for 'future'. Does NOT save to the database —
        app.py's /draw route is responsible for saving, so it's only saved once."""
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()
            card_data = data["cards"][0]
            card_name = card_data["name"]
            random_meaning = random.choice(["upright", "reversed"])
            if random_meaning == "upright":
                meaning = card_data["meaning_up"]
            else:
                meaning = card_data["meaning_rev"]
            card = Card(card_name, meaning, random_meaning)
            self.future.append(card)
            print(card.give_card())

    def get_oracle(self, lang="en"):
        """Fetches 3 cards (past/present/future) and generates the AI story.
        Does NOT save anything to the database — app.py's /draw route (oracle
        branch) is responsible for saving all 3 cards + the story, so nothing
        gets written twice."""
        try:
            response = requests.get("https://tarotapi.dev/api/v1/cards/random?n=3")
        except requests.exceptions.RequestException:
            raise TarotAPIError()
        else:
            data = response.json()

            card_data1 = data["cards"][0]
            card_name1 = card_data1["name"]
            random_meaning1 = random.choice(["upright", "reversed"])
            meaning1 = card_data1["meaning_up"] if random_meaning1 == "upright" else card_data1["meaning_rev"]
            card1 = Card(card_name1, meaning1, random_meaning1)
            self.past.append(card1)

            card_data2 = data["cards"][1]
            card_name2 = card_data2["name"]
            random_meaning2 = random.choice(["upright", "reversed"])
            meaning2 = card_data2["meaning_up"] if random_meaning2 == "upright" else card_data2["meaning_rev"]
            card2 = Card(card_name2, meaning2, random_meaning2)
            self.present.append(card2)

            card_data3 = data["cards"][2]
            card_name3 = card_data3["name"]
            random_meaning3 = random.choice(["upright", "reversed"])
            meaning3 = card_data3["meaning_up"] if random_meaning3 == "upright" else card_data3["meaning_rev"]
            card3 = Card(card_name3, meaning3, random_meaning3)
            self.future.append(card3)

            story = generate_oracle_story(meaning1, meaning2, meaning3, lang=lang)
            self.oracle_story = story