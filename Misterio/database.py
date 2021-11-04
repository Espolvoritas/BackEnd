from pony.orm import Database, PrimaryKey, Optional, Set, Required
from pony.orm import select, db_session, flush, count
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

class CardValue(Enum):
    pass

class Monster(CardValue):
    DRACULA = 1
    FRANKENSTEIN = 2
    WEREWOLF = 3
    GHOST = 4
    MUMMY = 5
    JEKYLL = 6

class Victim(CardValue):
    COUNT = 7
    COUNTESS = 8
    HOUSEKEEPER = 9
    BUTLER = 10
    MAIDEN = 11
    GARDENER = 12

class Room(CardValue):
    LOBBY = 13
    LAB = 14
    LIBRARY = 15
    CELLAR = 16
    ROOM = 17
    PANTHEON = 18
    HALL = 19
    CARTPORT = 20

class Card(db.Entity):
    cardId = PrimaryKey(int, auto=True)
    cardName = Optional(str)
    cardType = Optional(str)
    owners = Set("Player", reverse="cards")
    culpritOf = Set("Game", reverse="culprit")
    victimOf = Set("Game", reverse="victim")
    roomOf = Set("Game", reverse="room")

    def isMonster(self):
        return self.cardType == "Monster"
    
    def isVictim(self):
        return self.cardType == "Victim"

    def isRoom(self):
        return self.cardType == "Room"


class Game(db.Entity):
    game_id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required('Player', reverse='hostOf')
    players = Set('Player', reverse='lobby')
    currentPlayer = Optional('Player', reverse="currentPlayerOf")
    playerCount = Required(int, default=0)
    isStarted = Required(bool, default=False)
    culprit = Optional(Card, reverse="culpritOf")
    room = Optional(Card, reverse="roomOf")
    victim = Optional(Card, reverse="victimOf")
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

    def fillEnvelope(self):
        #Get the available cards
        victimCards = select(c for c in db.Card if c.cardType == "Victim")
        monsterCards = select(c for c in db.Card if c.cardType == "Monster")
        roomCards = select(c for c in db.Card if c.cardType == "Room")
        # Fill the "Misterio" envelope
        self.culprit=choice(list(monsterCards))
        self.room=choice(list(roomCards))
        self.victim=choice(list(victimCards))

    def shuffleDeck(self):
        self.fillEnvelope()
        envelope = select((g.victim,g.culprit,g.room) for g in Game if g.game_id == self.game_id)
        availableCards = list(select(c for c in db.Card if c not in envelope.first()))
        shuffle(availableCards)
        player = self.currentPlayer
        for card in availableCards:
            player.cards.add(card)
            player = player.nextPlayer
        minCards = count(player.cards)
        players = select(p for p in self.players if count(p.cards) == minCards)
        self.currentPlayer = choice(players)

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
    cards = Set(Card, reverse="owners")
    location = Optional("Cell", reverse="occupiers")
    trapped = Optional(bool)
    inRoom = Optional(bool)

    def setColor(self, color):
        self.color = color

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer


class Cell(db.Entity):
    cellId = PrimaryKey(int, auto=True)
    game = Optional(Game, reverse="board")
    occupiers = Optional(Player, reverse="location")
    neighbors = Set("Cell", reverse="neighbors")
    freeNeighbors = Set("Cell", reverse="freeNeighbors")
    isTrap = Optional(bool)


db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

# Functions to test and fill database

def fillCards():
    with db_session:
        for card in Monster:
            monster = Card(cardName=card.name, cardType="Monster")
        for card in Victim:
            victim = Card(cardName=card.name, cardType="Victim")
        for card in Room:
            room = Card(cardName=card.name, cardType="Room")

def fillColors():
    #Colors shouldn't be modified outside this session
    with db_session:
        for color in ColorCode:
            color = Color(colorName=color.name)

def clear_tables():
    db.Player.cards.drop_table(with_all_data=True)
    db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.drop_table(db.Card, if_exists=True, with_all_data=True)
    db.drop_table(db.Color, if_exists=True, with_all_data=True)
    db.create_tables()
    fillColors()
    fillCards()

clear_tables()