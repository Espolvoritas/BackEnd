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

class Cell(db.Entity):
    cellId = PrimaryKey(int, auto=True)
    neighbors = Set("Neighbor", reverse="neighborOf")
    occupiers = Set("Player", reverse="location")
    game = Optional("Game", reverse="board")

    x = Optional(int)
    y = Optional(int)

    isTrap = Optional(bool)
    roomName = Optional(str)


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
    isStarted = Required(bool, default=False)

    culprit = Optional(str)
    room = Optional(str)
    victim = Optional(str)
    board = Set("Cell", reverse="game")
    
    def addPlayer(self, player):
        if (self.playerCount <= 6):
            self.players.add(player)
            self.playerCount += 1   
        colors = self.getAvailableColors()
        if colors:
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

    location = Optional("Cell", reverse="occupiers")
    trapped = Optional(bool)
    inRoom = Optional(bool)

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer


class Neighbor(db.Entity):
    distance = Optional(int)
    cell = Optional(Cell)
    neighborOf = Optional(Cell)

db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

# Functions to test and fill database

def fillColors():
    #Colors shouldn't be modified outside this session
    with db_session:
        for color in ColorCode:
            color = Color(colorName=color.name)

def clear_tables():
    db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.drop_table(db.Color, if_exists=True, with_all_data=True)
    db.create_tables()
    fillColors()

clear_tables()