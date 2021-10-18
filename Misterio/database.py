from random import shuffle
from random import randint as roll

from pony.orm import Database, PrimaryKey, Optional, Set, Required
from pony.orm import select

db = Database()

class Game(db.Entity):
    gameId = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required('Player', reverse='hostOf')
    firstPlayer = Optional('Player', reverse='firstIn')
    players = Set('Player', reverse='lobby')
    playerCount = Required(int, default=0)
    isStarted = Required(bool)
    
    def addPlayer(self, player):
        if (self.playerCount < 6):
            self.players.add(player)
            self.playerCount += 1
        
    def getPlayers(self):
        return select(p for p in self.players)
        
    def sortPlayers(self):
        '''Assign each player who joined the game a '.nextPlayer' randomly.'''
        shuffledPlayers = list([p for p in self.players])
        shuffle(shuffledPlayers)
        for index, player in enumerate(shuffledPlayers):
            player.nextPlayer = shuffledPlayers[(index + 1) % len(shuffledPlayers)]

class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickname = Required(str)
    hostOf = Optional(Game)
    firstIn = Optional(Game)
    lobby = Optional(Game)
    nextPlayer = Optional('Player', reverse="previousPlayer")
    previousPlayer = Optional('Player', reverse="nextPlayer")
    currentDiceRoll = Optional(int)

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer
        # nextPlayer.previousPlayer = self

    def rollDice(self):
        self.currentDiceRoll = roll(1, 7)


db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

db.drop_table(Game, if_exists=True, with_all_data=True)
db.drop_table(Player, if_exists=True, with_all_data=True)

db.create_tables()
