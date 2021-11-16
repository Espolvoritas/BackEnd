import string
import random
from pony.orm import db_session
from fastapi.testclient import TestClient

import Misterio.database as db

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def add_player(player: db.Player, lobby_id: str):
    with db_session:  
	    game = db.Lobby.get(lobby_id=lobby_id)
	    game.add_player(player)

def create_players(quantity: int, lobby_id: int):
	player_list = []
	with db_session:
		for x in range(quantity):
			new_player = db.Player(nickname=get_random_string(6))
			add_player(new_player, lobby_id)
			player_list.append(new_player.nickname)
		return player_list

def create_game_post(nickname: str, client: TestClient):
	return client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": nickname}
				)

def start_game_post(player_id: int, client: TestClient):
	return client.post("/lobby/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json=f'{player_id}'
				)

def pick_color_put(player_id: int, color: int , client: TestClient):
	return client.put("/lobby/pickColor",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"player_id": player_id, "color": color}
				)

def suspicion_post(player_id: int, victim_id: int, monster_id: int, client: TestClient):
	return client.post("/gameBoard/checkSuspicion",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'player_id': player_id, 'victim_id': victim_id, 'monster_id': monster_id}
				)

def roll_dice_post(player_id: int, roll: int, client: TestClient):
	return client.post("/gameBoard/rollDice",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'player_id': player_id, 'roll': roll}
				)

def move_post(player_id: int, x: int, y: int, remaining: int,client: TestClient):
	return client.post("/gameBoard/moves",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'player_id': player_id, 'x': x, "y": y, "remaining": remaining}
				)

def accuse_post(player_id: int, room: int, monster: int, victim: int,client: TestClient):
	return client.post("/gameBoard/accuse",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'room': room, 'monster': monster, "victim": victim, "player_id": player_id}
				)