from enum import unique
from random import shuffle
from typing import Match
from pony.orm import Database, Required, Optional, PrimaryKey, Set, select

db = Database()

class Game(db.Entity):
    game_id = PrimaryKey(int, auto=True) 
    name = Required(str)
    capacity = Required(int)
    isStarted = Required(bool)
    players = Set('Player', reverse='lobby')
    host = Required('Player', reverse='hostOf')

    def addPlayer(self, player):
        self.players.add(player)

    def getPlayers(self):
        return select(p for p in self.players)


class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickname = Required(str)
    hostOf = Optional(Game)
    lobby = Optional(Game)
    previous: Required('Player', reverse="nextPlayer")
    nextPlayer: Required('Player', reverse="previous")
    currentRoll: Required(int)

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer


db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database


# como es cuando un jugador abandona la partida?

