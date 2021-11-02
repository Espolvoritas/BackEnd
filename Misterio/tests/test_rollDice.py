from fastapi.testclient import TestClient
from pony.orm import db_session, flush
import string
import logging
import random

import Misterio.database as db
from Misterio.server import app

client = TestClient(app)
logger = logging.getLogger("gameboard")


#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def add_player(nickName: str, game_id: int):
	with db_session:
		game = db.Game.get(game_id=game_id)
		player = db.Player(nickName=nickName)
		flush()
		game.addPlayer(player)

def create_players(quantity: int, game_id: int):
	player_list = []
	for x in range(quantity):
		new_player = get_random_string(6)
		add_player(new_player, game_id)
		player_list.append(new_player)
	return player_list

def create_new_game(nickName: str):
	return client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": nickName}
				)

def create_player():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']

def startGame(userID):
	return client.post("/lobby/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json=f'{userID}'
				)

def test_send_one_roll():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
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
	
	roll = random.randint(1,6)
	with db_session:
		current_player = db.Game.get(game_id=1).currentPlayer.player_id
		current_player_nickName = db.Game.get(game_id=1).currentPlayer.nickName
		next_player = db.Game.get(game_id=1).currentPlayer.nextPlayer.nickName
	with client.websocket_connect("/gameBoard/" + str(current_player)) as websocket1:
		try:
			data = websocket1.receive_json()
			assert current_player_nickName == data
			websocket1.send_text(roll)
			data = websocket1.receive_json()
			assert next_player == data
			websocket1.close()
		except KeyboardInterrupt:
			websocket1.close()
	with db_session:
		player = db.Player.get(player_id=current_player)
		curr_roll = player.currentDiceRoll
	assert curr_roll == roll

def test_send_one_roll_not_in_turn():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
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
	
	roll = random.randint(1,6)
	with db_session:
		wrong_player = db.Game.get(game_id=1).currentPlayer.nextPlayer.player_id
	with client.websocket_connect("/gameBoard/" + str(wrong_player)) as websocket1:
		try:
			websocket1.send_text(roll)
			websocket1.close()
		except KeyboardInterrupt:
			websocket1.close()
	with db_session:
		player = db.Player.get(player_id=wrong_player)
		#if current player is player 2
		assert player.currentDiceRoll is None