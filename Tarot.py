import requests
import random
import Tarot_database


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

    
class Card():
    def __init__(self, card_name, meaning, random_meaning):
        self.card_name = card_name
        self.meaning = meaning
        self.orientation = random_meaning

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
            self.future.append(card3)
            Tarot_database.save_reading(self.user_name, "future", card3.card_name, card3.meaning, card3.orientation)
            print(card3.give_card())


def main():
    while True:
        Tarot_database.create_table()
        user_name = input("Print your name: ")
        try:
            if user_name.isdigit() or not user_name:
                raise WrongNameError(user_name)
        except WrongNameError as error:
            print(error)
        else:
            break

    while True:
        gender = input("Print your gender (man/woman): ")
        try:
            if gender != "man" and gender != "woman":
                raise WrongGenderError(gender)
        except WrongGenderError as error:
            print(error)
        else:
            break

    me = User(user_name, gender)
    while True:
        do_next = input("What do you want next? Print 1 - draw a past, 2 - draw a present, 3 - draw a future, 4 - draw an oracle, 5 - see my past, 6 - see my present, 7 - see my future, 8 - see all my oracles, 9 - end session: ", )
        try:
            if do_next != '1' and do_next != '2' and do_next != '3' and do_next != '4' and do_next != '5' and do_next != '6' and do_next != '7' and do_next != '8' and do_next != '9':
                raise WrongDigitError(do_next)
        except WrongDigitError as error:
            print(error)
        else:
            if do_next == '1':
                me.get_past()
            if do_next == '2':
                me.get_present()
            if do_next == '3':
                me.get_future()
            if do_next == '4':
                me.get_oracle()  
            if do_next == '5':
                me.my_past()
            if do_next == '6':
                me.my_present()
            if do_next == '7':
                me.my_future()
            if do_next == '8':
                me.my_oracle()                  
            if do_next == '9':
                print("Thank you for using us!")
                break
                    

main()
# El = User("El", "man")
# El.get_future()
# El.get_future()
# El.my_future()

