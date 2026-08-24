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