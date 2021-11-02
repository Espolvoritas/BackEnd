from pony.orm import Database, PrimaryKey, Optional, Set, Required
from pony.orm import select, db_session
from random import shuffle, choice
from enum import Enum

db = Database()

class ColorCode(Enum):
    RED=1
    GREEN=2
    BLUE=3
    WHITE=4
    BLACK=5
    YELLOW=6
    PINK=7
    ORANGE=8


class Color(db.Entity):
    color_id = PrimaryKey(int, auto=True)
    colorName = Required(str)
    players = Set('Player', reverse='color')

class Game(db.Entity):
    game_id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required('Player', reverse='hostOf')
    players = Set('Player', reverse='lobby')
    currentPlayer = Optional('Player', reverse="currentPlayerOf")
    playerCount = Required(int, default=0)
    isStarted = Required(bool)
    
    def addPlayer(self, player):
        if (self.playerCount <= 6):
            self.players.add(player)
            self.playerCount += 1
        colors = self.getAvailableColors()
        player.setColor(choice(colors))
        
    def getPlayers(self):
        return select(p for p in self.players)

    def sortPlayers(self):
        '''Assign each player who joined the game a `.nextPlayer` randomly.'''
        shuffledPlayers = list([p for p in self.players])
        shuffle(shuffledPlayers)
        for index, player in enumerate(shuffledPlayers):
            player.nextPlayer = shuffledPlayers[(index + 1) % len(shuffledPlayers)]
        self.currentPlayer = shuffledPlayers[0]

    def getAvailableColors(self):
        #Returns a list of type Color elements that have not been assigned
        player_colors = (select (p.color for p in db.Player if p.lobby.game_id == self.game_id))
        colors = list(select(c for c in db.Color if c not in player_colors))
        return colors

class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickName = Required(str)
    hostOf = Optional(Game)
    lobby = Optional(Game)
    currentPlayerOf = Optional(Game, reverse="currentPlayer")
    nextPlayer = Optional('Player', reverse="previousPlayer")
    previousPlayer = Optional('Player', reverse="nextPlayer")
    currentDiceRoll = Optional(int)
    color = Optional(Color, reverse='players')

    def setColor(self, color):
        self.color = color

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer

db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

def clear_tables():
    db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.drop_table(db.Color, if_exists=True, with_all_data=True)
    db.create_tables()

clear_tables()
#Colors shouldn't be modified outside this session
with db_session:
    for color in ColorCode:
        color = Color(color=color.name)

