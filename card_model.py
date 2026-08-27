MAJOR_ARCANA_FILES = {
    "The Fool": "major_arcana_fool.webp",
    "The Magician": "major_arcana_magician.webp",
    "The High Priestess": "major_arcana_priestess.webp",
    "The Empress": "major_arcana_empress.webp",
    "The Emperor": "major_arcana_emperor.webp",
    "The Hierophant": "major_arcana_hierophant.webp",
    "The Lovers": "major_arcana_lovers.webp",
    "The Chariot": "major_arcana_chariot.webp",
    "Strength": "major_arcana_strength.webp",
    "The Hermit": "major_arcana_hermit.webp",
    "Wheel of Fortune": "major_arcana_fortune.webp",
    "Justice": "major_arcana_justice.webp",
    "The Hanged Man": "major_arcana_hanged.webp",
    "Death": "major_arcana_death.webp",
    "Temperance": "major_arcana_temperance.webp",
    "The Devil": "major_arcana_devil.webp",
    "The Tower": "major_arcana_tower.webp",
    "The Star": "major_arcana_star.webp",
    "The Moon": "major_arcana_moon.webp",
    "The Sun": "major_arcana_sun.webp",
    "Judgement": "major_arcana_judgement.webp",
    "The World": "major_arcana_world.webp",
}

MAJOR_ARCANA_ALIASES = {
    "the last judgment": "major_arcana_judgement.webp",
    "judgment": "major_arcana_judgement.webp",
    "fortitude": "major_arcana_strength.webp",
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
        return f"minor_arcana_{suit_code}_{rank_code}.webp"

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