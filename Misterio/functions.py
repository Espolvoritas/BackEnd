import string
import random
from pony.orm import db_session
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession
from pony.orm import get as dbget

import Misterio.database as db

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def cellByCoordinates(x, y):
	return dbget(c for c in db.Cell if c.x == x and c.y == y)

def add_player(player: db.Player, game_id: str):
    with db_session:  
	    game = db.Game.get(game_id=game_id)
	    game.addPlayer(player)

def receive_until_code(websocket: WebSocketTestSession, code:int):
	data = {"code": 0}
	while data["code"] != code:
		previousCode = data["code"]
		msg = websocket.receive_json()
		data.update(msg)
		print(str(previousCode) + " " + str(code))
		print(data)
		if not (previousCode & msg["code"]):
			data["code"] = previousCode | msg["code"]
	return data

def create_players(quantity: int, game_id: int):
	player_list = []
	with db_session:
		for x in range(quantity):
			new_player = db.Player(nickName=get_random_string(6))
			add_player(new_player, game_id)
			player_list.append(new_player.nickName)
		return player_list

def create_game_post(nickName: str, client: TestClient):
	return client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": nickName}
				)

def startGame_post(userID: int, client: TestClient):
	return client.post("/lobby/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json=f'{userID}'
				)

def pickColor_put(userID: int, color: int , client: TestClient):
	return client.put("/lobby/pickColor",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"player_id": userID, "color": color}
				)

def suspicion_post(userID: int, victimId: int, culpritId: int, client: TestClient):
	return client.post("/gameBoard/checkSuspicion",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'playerId': userID, 'victimId': victimId, 'culpritId': culpritId}
				)

def rollDice_post(userID: int, roll: int, client: TestClient):
	return client.post("/gameBoard/rollDice",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'playerId': userID, 'roll': roll}
				)

def move_post(userID: int, x: int, y: int, remaining: int,client: TestClient):
	return client.post("/gameBoard/moves",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'player_id': userID, 'x': x, "y": y, "remaining": remaining}
				)

def accuse_post(userID: int, room: int, monster: int, victim: int,client: TestClient):
	return client.post("/gameBoard/accuse",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={'room': room, 'monster': monster, "victim": victim, "userID": userID}
				)