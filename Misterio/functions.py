from pony.orm import db_session, select
from Misterio.constants import *
from Misterio.enums import Room
import Misterio.database as db

@db_session
def get_cell_by_coordinates(x, y):
    return select(c for c in db.Cell if c.x == x and c.y == y).first()

def get_room_cell_id(room_name: str):
    for room in Room:
        if room.name == room_name:
            return room.value

@db_session
def get_room_card_id(room_name: str):
    card_id = db.Card.get(card_name=room_name).card_id
    return card_id

def get_room_card_id(room_name: str):
    card_id = db.Card.get(card_name=room_name).card_id
    return card_id

@db_session
def get_position_list(lobby_id: int):
    position_list = []
    lobby = get_lobby_by_id(lobby_id)
    for player in list(lobby.players):
        position_list.append(
            {
                "player_id": player.player_id,
                 "color": player.color.color_id,
                 "x" : player.location.y, 
                 "y": player.location.x
            }
        )
    return position_list

@db_session
def set_player_status(player):
    global_stats = db.Stats.get(stats_id=1)
    cell = player.location
    if cell.cell_type == "TRAP":
        if player.trapped == trapped_status.NOT_TRAPPED.value:
            player.trapped = trapped_status.TRAPPED.value
            global_stats.trap_falls += 1 
        elif player.trapped == trapped_status.TRAPPED.value:
            player.trapped = trapped_status.CAN_LEAVE.value
    elif "PORTAL-" in cell.cell_type:
        player.in_portal = True
        

@db_session
def clear_player_status(player):
    player.trapped = trapped_status.NOT_TRAPPED.value
    player.in_portal = False

@db_session
def get_reachable(player_id: int):
    moves = []
    player = get_player_by_id(player_id)
    reachable_cells = player.location.get_reachable(player.current_dice_roll, player)
    if reachable_cells is not None:
        for cell, distance in reachable_cells:
            option = {"x": 0, "y": 0, "remaining": 0}
            #Inverted because keep logic working
            option["x"] = cell.y
            option["y"] = cell.x
            option["remaining"] = distance
            moves.append(option)
    return moves

@db_session
def get_next_turn(lobby_id: int):
    lobby = get_lobby_by_id(lobby_id)
    current_player = lobby.game.current_player
    lobby.game.current_player = current_player.next_player
    set_player_status(current_player)
    if lobby.game.current_player.alive and (lobby.game.current_player.trapped != trapped_status.TRAPPED.value):
        return lobby.game.current_player.nickname
    else:    
        return get_next_turn(lobby_id)

@db_session
def get_current_turn(lobby_id: int):
    lobby = get_lobby_by_id(lobby_id)
    return lobby.game.current_player.nickname

@db_session
def get_player_nickname(player_id: int):
    player = get_player_by_id(player_id)
    return player.nickname

@db_session
def get_player_color(player_id: int):
    player = get_player_by_id(player_id)
    return player.color.color_id

@db_session
def player_in_turn(player_id: int):
    player = get_player_by_id(player_id)
    lobby = player.lobby
    return player_id == lobby.game.current_player.player_id

@db_session
def get_card_list(player_id: int):
    cards = list(db.Player.get(player_id=player_id).cards)
    return list(c.card_id for c in cards)

@db_session
def all_dead(lobby_id: int):
    lobby = db.Lobby.get(lobby_id=lobby_id)
    players = lobby.players
    for player in players:
        if player.alive:
            return False
    return True

@db_session
def get_color_list(lobby_id: int):
    color_list = []
    lobby = db.Lobby.get(lobby_id=lobby_id)
    if lobby:
        color_query = lobby.get_available_colors()
        for c in color_query:
            color_list.append(c.color_id)
    return color_list

@db_session
def get_used_colors_list(lobby_id: int):
    lobby = get_lobby_by_id(lobby_id)
    color_list = []
    if lobby:
        color_query = list(select(p.color for p in lobby.players))
    for c in color_query:
        color_list.append(c.color_id)
    return color_list

# Database getters

@db_session
def get_lobby_by_id(lobby_id: int):
    lobby = db.Lobby.get(lobby_id=lobby_id)
    return lobby

@db_session
def get_player_by_id(player_id: int):
    player = db.Player.get(player_id=player_id)
    return player

@db_session
def get_card_by_id(card_id: int):
    card = db.Card.get(card_id=card_id)
    return card
