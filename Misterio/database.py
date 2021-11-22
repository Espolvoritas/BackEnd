from pony.orm import Database, PrimaryKey, Optional, Set, Required, Json
from pony.orm import select, db_session, count
from random import shuffle, choice
from datetime import datetime
from Misterio.board import make_board
from Misterio.enums import *
from Misterio.constants import trapped_status

db = Database()

class Color(db.Entity):
    color_id = PrimaryKey(int, auto=True)
    color_name = Required(str)

    #Relationship attributes
    players = Set("Player", reverse="color")

class Card(db.Entity):
    card_id = PrimaryKey(int, auto=True)
    card_name = Optional(str)
    card_type = Optional(str)
    misterio_monster = Set("Game", reverse="monster")
    misterio_victim = Set("Game", reverse="victim")
    misterio_room = Set("Game", reverse="room")
    owners = Set("Player", reverse="cards")

    def is_monster(self):
        return self.card_type == "MONSTER"
    
    def is_victim(self):
        return self.card_type == "VICTIM"

    def is_room(self):
        return self.card_type == "ROOM"

    def assign(self, player):
        player.cards.add(self)

class Lobby(db.Entity):
    lobby_id = PrimaryKey(int, auto=True) 
    name = Required(str)
    player_count = Required(int, default=0)
    is_started = Required(bool, default=False)
    password = Optional(str)
    #Relationship attributes
    host = Required("Player", reverse="host_of")
    players = Set("Player", reverse="lobby")
    game = Optional("Game", reverse="lobby")

    def add_player(self, player):
        if (self.player_count <= 6):
            self.players.add(player)
            self.player_count += 1   
        colors = self.get_available_colors()
        if colors:
            player.set_color(choice(colors))
    
    def get_available_colors(self):
        #Returns a list of type Color elements that have not been assigned
        player_colors = (select (p.color for p in Player if p.lobby.lobby_id == self.lobby_id))
        colors = list(select(c for c in Color if c not in player_colors))
        return colors

class Game(db.Entity):
    game_id = PrimaryKey(int, auto=True) 
    start_date = Required(datetime, default=datetime.utcnow())
    #Relationship attributes
    lobby = Required(Lobby, reverse="game")
    current_player = Optional("Player", reverse="current_player_of")
    monster = Optional(Card, reverse="misterio_monster")
    victim = Optional(Card, reverse="misterio_victim")
    room = Optional(Card, reverse="misterio_room")
    board = Set("Cell", reverse="game")

    def get_game_duration(self):
        finish_date = datetime.utcnow()
        duration = finish_date - self.start_date   
        return duration.total_seconds()

    def fill_envelope(self):
        #Get the available cards
        victim_cards = select(c for c in Card if c.card_type == "VICTIM")
        monster_cards = select(c for c in Card if c.card_type == "MONSTER")
        room_cards = select(c for c in Card if c.card_type == "ROOM")
        # Fill the "Misterio" envelope
        self.monster=choice(list(monster_cards))
        self.room=choice(list(room_cards))
        self.victim=choice(list(victim_cards))

    def shuffle_deck(self):
        self.fill_envelope()
        envelope = [self.monster, self.victim, self.room]
        available_cards = list(select(c for c in Card if c not in envelope))
        shuffle(available_cards)
        player = self.current_player
        for card in available_cards:
            player.cards.add(card)
            player = player.next_player
        min_cards = count(player.cards)
        players = list(select(p for p in self.lobby.players if count(p.cards) == min_cards))
        self.current_player = choice(players)

    def sort_players(self):
        shuffled_players = list([p for p in self.lobby.players])
        
        shuffle(shuffled_players)
        for index, player in enumerate(shuffled_players):
            player.set_next(shuffled_players[(index + 1) % len(shuffled_players)])
        self.current_player = shuffled_players[0]
 
    def set_starting_positions(self):
        players = list(select(p for p in self.lobby.players))
        entrances = list(select(c for c in Cell if c.cell_type == "START_CELL"))
        shuffle(players)
        shuffle(entrances)
        locations = zip(players, entrances)
        for p, e in locations:
            p.location = e
    
    def win_check(self, monster, victim, room):
        monster_correct = (self.monster.card_id == monster)
        victim_correct = (self.victim.card_id == victim)
        room_correct = (self.room.card_id == room)
        return (monster_correct and victim_correct and room_correct)

class Player(db.Entity):
    player_id = PrimaryKey(int, auto=True) 
    nickname = Required(str)
    alive = Required(bool, default=True)
    current_dice_roll = Optional(int, default=0)
    trapped = Required(int, default=0)
    in_portal = Required(bool, default=False)
    
    #Relationship attributes
    color = Optional(Color, reverse="players")
    next_player = Optional("Player", reverse="next_player_of")
    lobby = Optional(Lobby, reverse="players")
    location = Optional("Cell", reverse="occupiers")
    cards = Set(Card, reverse="owners")

    #Reverse Relationships
    host_of = Optional(Lobby, reverse="host")
    current_player_of = Optional(Game, reverse="current_player")
    next_player_of = Optional("Player", reverse="next_player")

    def set_color(self, color):
        self.color = color

    def set_next(self, next_player):
        self.next_player = next_player

    def set_roll(self, dice_roll):
        self.current_dice_roll = dice_roll

    def commit_die(self):
        self.alive=False

class Cell(db.Entity):
    cell_id = PrimaryKey(int, auto=True)
    x = Required(int)
    y = Required(int)
    room_name = Optional(str)
    cell_type = Required(str)
    
    #Relationship attributes
    game = Optional(Game, reverse="board")
    occupiers = Set(Player, reverse="location")
    neighbors = Set("Cell", reverse="neighbor_of")
    free_neighbors = Set("Cell", reverse="free_neighbor_of")
   
    #Reverse Relationships
    neighbor_of = Set("Cell", reverse="neighbors")
    free_neighbor_of = Set("Cell", reverse="free_neighbors")

    def get_neighbors(self):
        return [c for c in self.neighbors]

    def get_free_neighbors(self):
        return [c for c in self.free_neighbors]

    def is_special(self):
        return self.cell_type not in ["PLAIN"] and "START_CELL" not in self.cell_type

    def is_room(self):
        return self.cell_type == "ROOM"
    
    def is_trap(self):
        return self.cell_type == "TRAP"

    def get_reachable(self, moves, player):

        reachable = []

        if moves > 0:

            reachable = [(n, moves-1) for n in self.get_neighbors()]

            already = {e for e, c in reachable} | set([self])
            
            current = list(reachable)
            new = []
            while current:
                for c, d in current:
                    if d != 0:
                        new = new + [(n, d-1) for n in c.get_neighbors() if n not in already]
                        #new = new + [(fn, d) for fn in c.getFreeNeighbors() if fn not in already]

                reachable = reachable + list(new)
                already = already | {c for c, d in new}
                current = list(new)
                new = list()
            
            if ("PORTAL-" in player.location.cell_type) and (player.in_portal):
                reachable = reachable + [(fn, moves) for fn in self.get_free_neighbors()]

            if (player.location.cell_type == "TRAP") and (player.trapped == trapped_status.CAN_LEAVE.value):
                reachable = reachable + [(fn, moves) for fn in self.get_free_neighbors()]

        if ("ENTRANCE-" in player.location.cell_type) or (player.location.cell_type=="ROOM"):
            reachable =  reachable + [(fn, moves) for fn in self.get_free_neighbors()]
    
        return reachable

class Stats(db.Entity):
    stats_id = PrimaryKey(int)
    won_games = Required(int, default=0)
    lost_games = Required(int, default=0)
    right_accusations = Required(int, default=0)
    wrong_accusations = Required(int, default=0)
    suspicions_made = Required(int, default=0)
    trap_falls = Required(int, default=0)
    game_data = Required(Json, default = {})

    def most_frequent(self, List):
        counter = 0
        elem = List[0]["id"]
        for i in List:
            curr_frequency = i["total"]
            if(curr_frequency > counter):
                counter = curr_frequency
                elem = i["id"]
        return elem

    def get_average_game_time(self):
        average = sum(self.game_data["time"])/len(self.game_data["time"])
        hours = divmod(average, 3600)
        minutes = divmod(hours[1],60)
        seconds = divmod(minutes[1],1)
        avg_time = (hours[0], minutes[0], seconds[0])
        return avg_time

    def find(self, lst, key, value):
        for i, dic in enumerate(lst):
            if dic[key] == value:
                return i
        return -1


    def add_monster(self, monster):
        index = self.find(self.game_data["envelope_monsters"], "id", monster)
        self.game_data["envelope_monsters"][index]["total"] += 1

    def add_victim(self, victim):
        index = self.find(self.game_data["envelope_victims"], "id", victim)
        self.game_data["envelope_victims"][index]["total"] += 1

    def add_room(self, room):
        index = self.find(self.game_data["envelope_rooms"], "id", room)
        self.game_data["envelope_rooms"][index]["total"] += 1

    def add_color(self, color):
        index = self.find(self.game_data["colors"], "id", color)
        self.game_data["colors"][index]["total"] += 1

    def envelope_top_cards(self):
        top_monster =  self.most_frequent(self.game_data["envelope_monsters"])
        top_victim = self.most_frequent(self.game_data["envelope_victims"])
        top_room = self.most_frequent(self.game_data["envelope_rooms"])
        return top_monster, top_victim, top_room

    def most_chosen_color(self):
        return self.most_frequent(self.game_data["colors"])
    
db.bind("sqlite", "database.sqlite", create_db=True)  # Connect object `db` with database.
db.generate_mapping(create_tables=True)  # Generate database

#Global stats table
with db_session:
    global_stats = Stats.get(stats_id=1)
    if global_stats is None:
        global_stats = Stats(stats_id=1)
        global_stats.game_data = {
            "time": [],
            "colors": [],
            "envelope_monsters": [],
            "envelope_victims": [],
            "envelope_rooms": []
        }
        for m,v in zip(Monster, Victim):
            monster = {"id": m.value, "total": 0}
            victim = {"id": v.value, "total": 0}
            global_stats.game_data["envelope_monsters"].append(monster)
            global_stats.game_data["envelope_victims"].append(victim)

        for r in Room:
            room = {"id": r.value, "total": 0}
            global_stats.game_data["envelope_rooms"].append(room)

        for c in ColorCode:
            color = {"id": c.value, "total": 0}
            global_stats.game_data["colors"].append(color)


# Functions to test and fill database
def fill_cards():
    with db_session:
        for card in Monster:
            Card(card_name=card.name, card_type="MONSTER")
        for card in Victim:
            Card(card_name=card.name, card_type="VICTIM")
        for card in Room:
            Card(card_name=card.name, card_type="ROOM")
        for card in Salem:
            Card(card_name=card.name, card_type="SALEM")
            
def fill_colors():
    #Colors shouldn"t be modified outside this session
    with db_session:
        for color in ColorCode:
            color = Color(color_name=color.name)

def fill_cells():
    room_names = [r.name for r in Room]

    cells, neighbors, free_neighbors = make_board()
    cell_index = {}
    with db_session:
        for cx, cy, t in cells:
            cell_index[(cx, cy, t)] = Cell(x=cx, y=cy, cell_type=t)

            if t in room_names:
                cell_index[(cx, cy, t)].room_name = t
                cell_index[(cx, cy, t)].cell_type = "ROOM"
                cell_index[(cx, cy, t)].is_room = True

        for c in cells:
            for n in neighbors[c]:
                cell_index[c].neighbors.add(cell_index[n])

        for c in cells:
            for fn in free_neighbors[c]:
                cell_index[c].free_neighbors.add(cell_index[fn])
        
def clear_tables():
    Player.cards.drop_table(with_all_data=True)
    Cell.neighbors.drop_table(with_all_data=True)
    Cell.free_neighbors.drop_table(with_all_data=True)
    db.drop_table(Player, if_exists=True, with_all_data=True)
    db.drop_table(Game, if_exists=True, with_all_data=True)
    db.drop_table(Lobby, if_exists=True, with_all_data=True)
    db.drop_table(Card, if_exists=True, with_all_data=True)
    db.drop_table(Color, if_exists=True, with_all_data=True)
    db.drop_table(Cell, if_exists=True, with_all_data=True)

    db.create_tables()
    fill_colors()
    fill_cards()
    fill_cells()

clear_tables()
