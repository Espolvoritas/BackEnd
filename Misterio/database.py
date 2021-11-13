from pony.orm import Database, PrimaryKey, Optional, Set, Required
from pony.orm import select, db_session, flush, count
from random import shuffle, choice
from enum import Enum
from pony.orm import flush
from random import shuffle, choice

from Misterio.board import make_board
from Misterio.enums import *

db = Database()

class Color(db.Entity):
    color_id = PrimaryKey(int, auto=True)
    colorName = Required(str)
    players = Set('Player', reverse='color')

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

    def assign(self, player):
        player.cards.add(self)

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
        players = list(select(p for p in self.players if count(p.cards) == minCards))
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

    def setStartingPositions(self):
        players = list(select(p for p in self.players))
        entrances = list(select(c for c in Cell if c.cellType == "entrance"))
        shuffle(players)
        shuffle(entrances)
        locations = zip(players, entrances)
        for p, e in locations:
            p.location = e

class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickName = Required(str)
    hostOf = Optional(Game)
    lobby = Optional(Game)
    alive = Required(bool, default=True)
    currentPlayerOf = Optional(Game, reverse="currentPlayer")
    nextPlayer = Optional('Player', reverse="previousPlayer")
    previousPlayer = Optional('Player', reverse="nextPlayer")
    currentDiceRoll = Optional(int, default=0)
    color = Optional(Color, reverse='players')
    cards = Set(Card, reverse="owners")
    location = Optional("Cell", reverse="occupiers")
    trapped = Optional(bool)
    inRoom = Optional(bool)

    def setColor(self, color):
        self.color = color

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer

    def commitDie(self):
        self.alive=False

class Cell(db.Entity):
    # The neighbors field stores the set of immediately adjacent cells
    # which require players to spend a move when changing positions.
    # freeNeighbors stores the set of adjacent cells which
    # do not require players to spend a move (for instance,
    # moving to a trap from another is a "free" move, same as moving from
    # a room entrance to the room it leads to)
    cellId = PrimaryKey(int, auto=True)
    game = Optional(Game, reverse="board")
    occupiers = Set(Player, reverse="location")
    neighbors = Set("Cell", reverse="neighborOf")
    neighborOf = Set("Cell", reverse="neighbors")
    freeNeighbors = Set("Cell", reverse="freeNeighborOf")
    freeNeighborOf = Set("Cell", reverse="freeNeighbors")
    isTrap = Optional(bool)
    isRoom = Optional(bool)
    roomName = Optional(str)
    x = Optional(int)
    y = Optional(int)
    cellType = Optional(str)

    def getNeighbors(self):
        return [c for c in self.neighbors]

    def getFreeNeighbors(self):
        return [c for c in self.freeNeighbors]

    def isSpecial(self):
        return self.cellType not in ["plain"] and "entrance" not in self.cellType

    def getReachable(self, moves):

        if moves == 0:
            return [(fn, 0) for fn in self.getFreeNeighbors()]

        if moves > 0:

            reachable = [(n, moves-1) for n in self.getNeighbors()]
            reachable = reachable + [(fn, moves) for fn in self.getFreeNeighbors()]

            already = {e for e, c in reachable} | set([self])
            special = {e for e, c in reachable if e.isSpecial()}
            
            current = list(reachable)
            new = []

            while current:

                for c, d in current:
                    if not c.isTrap:
                        if d != 0:
                            new = new + [(n, d-1) for n in c.getNeighbors() if n not in already]
                        #new = new + [(fn, d) for fn in c.getFreeNeighbors() if fn not in already]

                reachable = reachable + list(new)
                already = already | {c for c, d in new}
                current = list(new)
                new = list()

            print(reachable)

            return reachable

db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

# Functions to test and fill database
def fillCards():
    with db_session:
        for card in Monster:
            Card(cardName=card.name, cardType="Monster")
        for card in Victim:
            Card(cardName=card.name, cardType="Victim")
        for card in Room:
            Card(cardName=card.name, cardType="Room")

def fillCards():
    with db_session:
        for card in Monster:
            monster = Card(cardName=card.name, cardType="Monster")
        for card in Victim:
            victim = Card(cardName=card.name, cardType="Victim")
        for card in Room:
            room = Card(cardName=card.name, cardType="Room")

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

def fillCells():
    roomNames = [r.name for r in Room]

    cells, neighbors, freeNeighbors = makeBoard()
    cellIndex = {}

    with db_session:
        for cx, cy, t in cells:
            cellIndex[(cx, cy, t)] = Cell(x=cx, y=cy, cellType=t)

            if t in roomNames:
                cellIndex[(cx, cy, t)].roomName = t
                cellIndex[(cx, cy, t)].cellType = "room"
                cellIndex[(cx, cy, t)].isRoom = True
            if "trap" in t:
                cellIndex[(cx, cy, t)].isTrap = True


        for c in cells:
            for n in neighbors[c]:
                cellIndex[c].neighbors.add(cellIndex[n])


        for c in cells:
            for fn in freeNeighbors[c]:
                cellIndex[c].freeNeighbors.add(cellIndex[fn])
        


def clear_tables():
    db.Player.cards.drop_table(with_all_data=True)
    db.Cell.neighbors.drop_table(with_all_data=True)
    db.Cell.freeNeighbors.drop_table(with_all_data=True)
    db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.drop_table(db.Card, if_exists=True, with_all_data=True)
    db.drop_table(db.Color, if_exists=True, with_all_data=True)
    db.drop_table(db.Cell, if_exists=True, with_all_data=True)

    db.create_tables()
    fillColors()
    fillCards()
    fillCells()

clear_tables()
