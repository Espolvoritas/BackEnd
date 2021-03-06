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

def test_send_one_roll():
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
	
	roll = random.randint(1,6)
	with db_session:
		current_player = db.Game.get(game_id=game_id).currentPlayer
		current_player_nickName = current_player.nickName
		next_player = current_player.nextPlayer

	print(current_player)
	with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
		data = websocket1.receive_json()
		print(data)
		with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
			#data = websocket1.receive_json()
			#print(data)
			data = websocket2.receive_json()
			print(data)
			try:
				assert current_player_nickName == data['currentPlayer']
				response = rollDice_post(current_player.player_id, roll, client)
				assert (response.status_code == 200)
				print(response)
				#assert next_player == data['currentPlayer']
				websocket2.close()
				data = websocket1.receive_json()
				print(data)
				websocket1.close()
			except KeyboardInterrupt:
				websocket1.close()
	with db_session:
		player = db.Player.get(player_id=current_player.player_id)
		curr_roll = player.currentDiceRoll
	assert curr_roll == roll

def test_send_one_roll_not_in_turn():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1,game_id)
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
	
	roll = random.randint(1,6)
	with db_session:
		wrong_player = db.Game.get(game_id=1).currentPlayer.nextPlayer.player_id
	with client.websocket_connect("/gameBoard/" + str(wrong_player)) as websocket1:
		try:
			response = rollDice_post(wrong_player, roll, client)
			assert (response.status_code == 403)
			websocket1.close()
		except KeyboardInterrupt:
			websocket1.close()

	with db_session:
		player = db.Player.get(player_id=wrong_player)
		#if current player is player 2
		assert player.currentDiceRoll == 0