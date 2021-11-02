from pony.orm import Database, PrimaryKey, Optional, Set, Required
from pony.orm import select

from random import shuffle
from collections import defaultdict
from itertools import product

db = Database()

class Card(db.Entity):
    cardId = PrimaryKey(int, auto=True)
    player = Optional("Player", reverse="cards")
    cardType = Optional(str)
    cardName = Optional(str)


class Game(db.Entity):
    game_id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required('Player', reverse='hostOf')
    players = Set('Player', reverse='lobby')
    currentPlayer = Optional('Player', reverse="currentPlayerOf")
    playerCount = Required(int, default=0)
    isStarted = Required(bool)

    culprit = Optional(str)
    room = Optional(str)
    victim = Optional(str)
    board = Set("Cell", reverse="game")
    
    def addPlayer(self, player):
        if (self.playerCount <= 6):
            self.players.add(player)
            self.playerCount += 1
        
    def getPlayers(self):
        return select(p for p in self.players)

    def sortPlayers(self):
        '''Assign each player who joined the game a `.nextPlayer` randomly.'''
        shuffledPlayers = list([p for p in self.players])
        shuffle(shuffledPlayers)
        for index, player in enumerate(shuffledPlayers):
            player.nextPlayer = shuffledPlayers[(index + 1) % len(shuffledPlayers)]
        self.currentPlayer = shuffledPlayers[0]


class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickName = Required(str)
    hostOf = Optional(Game)
    lobby = Optional(Game)
    currentPlayerOf = Optional(Game, reverse="currentPlayer")
    nextPlayer = Optional('Player', reverse="previousPlayer")
    previousPlayer = Optional('Player', reverse="nextPlayer")
    currentDiceRoll = Optional(int)

    location = Optional("Cell", reverse="occupiers")
    trapped = Optional(bool)
    inRoom = Optional(bool)

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer


db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

db.drop_table(Game, if_exists=True, with_all_data=True)
db.drop_table(Player, if_exists=True, with_all_data=True)

db.create_tables()
