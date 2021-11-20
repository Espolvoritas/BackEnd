from fastapi.testclient import TestClient
from pony.orm import db_session
import string
import random # define the random module  

from Misterio.server import app
import Misterio.database as db
from Misterio.functions import *

client = TestClient(app)

#make sure that no player gets an envelope card
def test_envelope():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1,game_id)
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
			with db_session:
				playerCards = []
				game = db.Game.get(game_id=game_id)
				for player in expectedPlayers:
					playerCards.append(list(db.Player.get(nickName=player).cards))
				assert game.culprit not in playerCards
				assert game.room not in playerCards
				assert game.victim not in playerCards
			websocket2.close()
			data = receive_until_code(websocket1, 4096)
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

#make sure that no player gets a duplicated cars
def test_duplication():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1,game_id)
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
			with db_session:
				game = db.Game.get(game_id=game_id)
				cards1 = list(db.Player.get(nickName=host).cards)
				cards2 = list(db.Player.get(nickName=expectedPlayers[1]).cards)
				for card in cards1:
					assert card not in cards2
			websocket2.close()
			data = receive_until_code(websocket1, 4096)
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

def test_random_first():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1,game_id)
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
			with db_session:
				first_player = db.Game.get(game_id=game_id).currentPlayer
			websocket2.close()
			data = receive_until_code(websocket1, 4096)
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1,game_id)
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
			with db_session:
				second_player = db.Game.get(game_id=game_id).currentPlayer
			assert first_player != second_player
			websocket2.close()
			data = receive_until_code(websocket1, 4096)
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	