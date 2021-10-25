from server import app
from fastapi.testclient import TestClient
import string    
import random # define the random module  
import database as db
from fastapi import WebSocketDisconnect
import pytest
from pony.orm import db_session

client = TestClient(app)

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    
    db.db.create_tables()

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

@db_session
def add_player(nickName: str, game_id: int):
	game = db.Game.get(game_id=game_id)
	player = db.Player(nickName=nickName)
	game.addPlayer(player)

def create_players(quantity: int, game_id: int):
	player_list = []
	for x in range(quantity):
		new_player = get_random_string(6)
		add_player(new_player, game_id)
		player_list.append(new_player)
	return player_list

def create_new_game(nickName: str):
	return client.post("/game/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": nickName}
				)

def startGame(userID):
	return client.post("/game/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json=f'{userID}'
				)

def test_start_game_one_player():
	clear_tables()
	host = get_random_string(6)
	response = create_new_game(host)
	
	assert response.status_code == 201
	response = client.post("/game/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json='1'
				)
	print(response)
	assert response.status_code == 405


def test_startGame_two_players():
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/game/getPlayers/1") as websocket1, \
		client.websocket_connect("/game/getPlayers/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected
			data = websocket2.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected

			response = startGame(1)
			assert response.status_code == 200
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

def test_startGame_not_host():
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/game/getPlayers/1") as websocket1, \
		client.websocket_connect("/game/getPlayers/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected
			data = websocket2.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected

			response = startGame(2)
			assert response.status_code == 403
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close