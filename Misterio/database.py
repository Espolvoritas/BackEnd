from pony.orm import Database, PrimaryKey, Optional, Set, Required
from pony.orm import select

from random import shuffle
from collections import defaultdict
from itertools import product

db = Database()

class Cell(db.Entity):
    cellId = PrimaryKey(int, auto=True)
    neighbors = Set("Neighbor", reverse="neighborOf")
    occupiers = Set("Player", reverse="location")
    game = Optional("Game", reverse="board")

    # Estos x e y ayudarian a interfacear con el front
    x = Optional(int)
    y = Optional(int)

    isTrap = Optional(bool)
    # Se podria agregar un `isRoom = Optional(bool)`, pero
    # es redundante (se puede hacer bool(self.roomName), me parece,
    # porque None es un valor falsy y cualquier string es truthy)

    roomName = Optional(str)

    # se modela la trampa y los "portales" (tarantula, vampiro y demas)
    # simplemente haciendo que la distancia entre portales iguales es 0, 
    # y entre trampas también

    # eso se "hardcodea" programaticamente al crear el tablero


class Card(db.Entity):
    cardId = PrimaryKey(int, auto=True)
    player = Optional("Player", reverse="cards")
    cardType = Optional(str) # should be one of "victim", "monster" and "room"
    cardName = Optional(str)


def floydWarshall(distances):
    '''Input a dictionary whose keys are pairs of cell coordinates
    and return a dictionary with the minimum distance between each pair
    of vertices'''
    pass

def makeBoard(self):
    # lo haces una vez, lo serializas y lo lees

    entrances = [(0, 6), (0, 13), 
                 (6, 0), (13, 0), 
                 (6, 19), (13, 19),
                 (19, 13), (19, 6)]
    
    roomEntrances = [(4, 6, "vestíbulo"), (6, 10, "vestíbulo"),
                     (4, 13, "vestíbulo"), (6, 2, "cochera"),
                     (13, 4, "biblioteca"), (13, 10, "panteón"),
                     (16, 13, "panteón"), (15, 6, "panteón"),
                     (13, 16, "laboratorio"),
                     (10, 13, "salón"), (6, 15, "bodega")]

    rooms = [["1", "2", "3"], ["4", "M", "6"], ["7", "8", "9"]]
    roomEntrances = {(i, j): "bodega", (), (), (), ()}
    board = [["" for i in range(0, 20)] for j in range(0, 20)]
    coordinates = [(x, y) for x in range(0, 19) for y in range(0, 19)]
    distances = defaultdict(lambda: defaultdict(lambda : -1))
    cells = []
        
    for x, y in coordinates:
                
        isTrap = x % 6 == 0 and y % 6 == 0
        isPlain = x % 6 == 0 or y % 6 == 0 and not isTrap
        # isPortal = viaje
        isRoom = not isPlain and not isTrap # and not isPortal

        if isTrap:
            board[x][y] = "#"
            cells.append(("trap", x, y))
            self.board.add(Cell(x=x, y=y, isTrap=True))

        if isPlain:
            board[x][y] = "-"
            cells.append(("plain", x, y))

        if isRoom:
            roomX = int(x / 6)
            roomY = int(y / 6)
            roomName = rooms[roomX][roomY]
            board[x][y] = roomName
            cells.append((roomName, x, y))

    # parte sin testear de esto so far
    roomNames = sum(rooms, [])
    plainCells = [c for c in cells if c[0] == "plain"]
    traps = [c for c in cells if c[0] == "trap"]

        # creo que va a ser mas facil con le algoritmo de Floyd
        # porque la distancia cero entre portales y trampas cambia
        # la distancia!

    for t, x, y in cells:
        for s, w, z in cells:

            distance = abs(x - w) + abs(y - z)

            if t == "plain" and s in ["trap", "plain"] and distance == 1:
                distances[(t, x, y)][(s, w, z)] = distance
                
            if t == s and s == "trap":
                distances[(t, x, y)][(s, w, z)] = 0

            if t in roomNames and s in roomNames and t == s:
                distances[(t, x, y)][(s, w, z)] = 0

    for (i, j) in entrances.keys():
        distances[()][()] = 1

    distances = floydWarshall(distances)

class Game(db.Entity):
    game_id = PrimaryKey(int, auto=True) 
    name = Required(str)
    host = Required('Player', reverse='hostOf')
    players = Set('Player', reverse='lobby')
    currentPlayer = Optional('Player', reverse="currentPlayerOf")
    playerCount = Required(int, default=0)
    isStarted = Required(bool)

    # New properties
    color = Optional(str)
    culprit = Optional(str)
    room = Optional(str)
    victim = Optional(str)
    board = Set("Cell", reverse="")
    
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

    # New methods

    # Son públicas las repuestas a las sospechas?
    
    def checkSuspicion(self, culprit, victim, room, respondee):
        suspectedCards = {culprit, victim, room}
        respondeeCards = set([c.id for c in respondee.cards])
        cardIntersection = suspectedCards & respondeeCards
        isSkippable = bool(cardIntersection)
        # if cardIntersection is empty, the respondee can be automatically skipped
        return cardIntersection, isSkippable

    def checkAccustion(self, culprit, victim, room, player):
        culpritMatches = culprit == self.culprit
        roomMatches = room == self.room
        victimMatches = victim == self.victim

        isSkippable = bool(cardIntersection)
        # if cardIntersection is empty, the respondee can be automatically skipped
        return cardIntersection, isSkippable

        # Casi trato de agregar una funcion para hacer la ronda
        # de sospechas
        # Pero a eso lo maneja el servidor, no la base de datos!
        # la base de datos solo tiene que revisar si hay interseccion entre
        # las cartas bajo sospecha y las cartas del respondee


class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickName = Required(str)
    hostOf = Optional(Game)
    lobby = Optional(Game)
    currentPlayerOf = Optional(Game, reverse="currentPlayer")
    nextPlayer = Optional('Player', reverse="previousPlayer")
    previousPlayer = Optional('Player', reverse="nextPlayer")
    currentDiceRoll = Optional(int)

    # Proposed properties
    # cards = Set(str) # asi no tenes que tener ids y eso!!
    location = Optional("Cell", reverse="occupiers")
    trapped = Optional(bool)
    inRoom = Optional(bool)

    def setNext(self, nextPlayer):
        self.nextPlayer = nextPlayer

    # Proposed methods
    def getMoves(self):
        return select(n for n in self.location.neighbors if n.distance < self.currentDiceRoll)
        # No sé si debería devolver un select o una lista -- la lista es un objeto de python común,
        # el resultado de select no se si existe fuera de `with db_session`
        # En ese caso tambien habria que devolver el id del vecino y no solo el vecino

    def move(self, cell):
        self.location = cell
        if cell.isTrap:
            self.trapped = True
        if cell.roomName:
            self.inRoom = True

    def accuse(self, culprit, victim):
        if self.inRoom:
            room = self.location.roomName
            self.lobby.checkAccusation(culprit, victim, room)
        else:
            pass #Handle exception properly

    def suspect(self, culprit, victim):
        if self.inRoom:
            room = self.location.roomName
            self.lobby.checkSuspicion(culprit, victim, room, self.nextPlayer)
        else:
            pass #Handle exception properly

class Neighbor(db.Entity):
    distance = Optional(int)
    cell = Optional(Cell)
    neighborOf = Optional(Cell)

db.bind('sqlite', 'database.sqlite', create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

db.drop_table(Game, if_exists=True, with_all_data=True)
db.drop_table(Player, if_exists=True, with_all_data=True)

db.create_tables()
