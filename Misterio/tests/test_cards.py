import unittest
import Misterio.database as db
from pony.orm import Database, db_session
from pony.orm import select, flush, commit

db.clear_tables()

def test_card_existence():
    card_names = """
    DRACULA
    FRANKENSTEIN
    WEREWOLF
    GHOST
    MUMMY
    JEKYLL
    COUNT
    COUNTESS
    HOUSEKEEPER
    BUTLER
    MAIDEN
    GARDENER
    LOBBY
    LAB
    LIBRARY
    CELLAR
    ROOM
    PANTHEON
    HALL
    GARAGE
    SALEM
    """

    allCardNames = set([n.strip() for n in card_names.split("\n") if len(n.strip()) > 0])
    foundCards = set()

    with db_session:
        cards = select(c for c in db.Card)
        for c in cards:
            assert(c.card_name in allCardNames)
            foundCards.add(c.card_name)

        assert(allCardNames == foundCards)
