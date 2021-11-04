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

def add_player(player: db.Player, game_id: str):
    with db_session:  
	    game = db.Game.get(game_id=game_id)
	    game.addPlayer(player)

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

def startGame_post(userID, client: TestClient):
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