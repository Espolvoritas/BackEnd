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

def test_right_accusation():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1, game_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame_post(1, client)
			assert response.status_code == 200
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

	with db_session:
		game = db.Game.get(game_id=game_id)
		current_player = game.currentPlayer
		current_player_nickName = current_player.nickName
		next_player = current_player.nextPlayer
		room = game.room.cardId
		monster = game.culprit.cardId
		victim = game.victim.cardId

	with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
		data = websocket1.receive_json()
		with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
			#data = websocket1.receive_json()
			data = websocket2.receive_json()
			try:
				assert current_player_nickName == data['currentPlayer']
				accuse_post(current_player.player_id,room, monster, victim, client)
				data = websocket1.receive_json()
				assert data['data']['won'] == True
				websocket2.close()
				data = websocket1.receive_json()
				websocket1.close()
			except KeyboardInterrupt:
				websocket1.close()

def test_wrong_accusation():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1, game_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame_post(1, client)
			assert response.status_code == 200
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

	with db_session:
		game = db.Game.get(game_id=game_id)
		current_player = game.currentPlayer
		current_player_nickName = current_player.nickName
		next_player = current_player.nextPlayer
		room = game.room.cardId
		monster = game.culprit.cardId
		victim = game.victim.cardId

	with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
		data = websocket1.receive_json()
		with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
			#data = websocket1.receive_json()
			data = websocket2.receive_json()
			try:
				assert current_player_nickName == data['currentPlayer']
				accuse_post(current_player.player_id,room, (monster-1), victim, client)
				data = websocket1.receive_json()
				assert data['data']['won'] == False
				websocket2.close()
				data = websocket1.receive_json()
				websocket1.close()
			except KeyboardInterrupt:
				websocket1.close()