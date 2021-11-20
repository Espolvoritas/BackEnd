from fastapi.testclient import TestClient
from pony.orm import db_session, flush
import string
import logging
import random
from Misterio.functions import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)
logger = logging.getLogger("gameboard")

@db_session
def find_entrance(movement):
	for possibility in movement:
		cell = cellByCoordinates(possibility['x'], possibility['y'])
		if 'entrance- ' in cell.cellType :
			return possibility

@db_session
def find_room(movement):
	for possibility in movement:
		cell = cellByCoordinates(possibility['x'], possibility['y'])
		if 'room' == cell.cellType :
			return possibility

def test_bad_move():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1, game_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame_post(1, client)
			assert response.status_code == 200
			websocket2.close()
			data = receive_until_code(websocket1, 4096)
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

		roll = random.randint(1,6)
	with db_session:
		current_player = db.Game.get(game_id=game_id).currentPlayer
		current_player_nickName = current_player.nickName
		next_player = current_player.nextPlayer

	with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
		data = websocket1.receive_json()
		with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
			#data = websocket1.receive_json()
			data = websocket2.receive_json()
			try:
				assert current_player_nickName == data['currentPlayer']
				response = rollDice_post(current_player.player_id, roll, client)
				assert (response.status_code == 200)
				response = move_post(current_player.player_id, 999, 999, 0,client)
				assert response.status_code == 400
				websocket2.close()
				websocket1.close()
			except KeyboardInterrupt:
				websocket2.close()
				websocket1.close()

def test_move():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1, game_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame_post(1, client)
			assert response.status_code == 200
			websocket2.close()
			data = receive_until_code(websocket1, 4096)
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

		roll = random.randint(1,6)
	with db_session:
		current_player = db.Game.get(game_id=game_id).currentPlayer
		current_player_nickName = current_player.nickName
		next_player = current_player.nextPlayer

	with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
		data = websocket1.receive_json()
		with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
			#data = websocket1.receive_json()
			data = websocket2.receive_json()
			try:
				assert current_player_nickName == data['currentPlayer']
				response = rollDice_post(current_player.player_id, roll, client)
				assert (response.status_code == 200)
				possible_moves = response.json()['moves']
				movement = random.choice(possible_moves)
				response = move_post(current_player.player_id, movement['x'], movement['y'], movement['remaining'],client)
				assert response.status_code == 200
				websocket2.close()
				websocket1.close()
			except KeyboardInterrupt:
				websocket2.close()
				websocket1.close()