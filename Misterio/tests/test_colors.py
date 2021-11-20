from fastapi.testclient import TestClient
from pony.orm import db_session, flush, select
from typing import Match
import string
import pytest
import random # define the random module  
from fastapi import WebSocketDisconnect
from Misterio.functions import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

def test_joinColors():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)

	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			with db_session:
				player1 = db.Player.get(nickName=expectedPlayers[0])
				player2 = db.Player.get(nickName=expectedPlayers[1])

				color1, color2 = player1.color, player2.color

			assert color1 is not None
			assert color2 is not None
			
			data = websocket1.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
				assert player['Color'] not in data['data']['colors']

			data2 = websocket2.receive_json()
			for player, expected in zip(data2['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
				assert player['Color'] not in data2['data']['colors']

			
			websocket2.close()
			assert color2.color_id not in data['data']['colors']

			data = websocket1.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
				assert player['Color'] not in data['data']['colors']
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	db.clear_tables()

def test_change_color():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	
	with client.websocket_connect("/lobby/1") as websocket1:
		expectedPlayers = create_players(1,game_id)
		expectedPlayers.insert(0,host)
		with db_session:
				player1 = db.Player.get(nickName=expectedPlayers[0])
				player2 = db.Player.get(nickName=expectedPlayers[1])
				player1id = player1.player_id
				player2id = player2.player_id
				color1, color2 = player1.color.color_id, player2.color.color_id
				expected_colors = [color1, color2]
		data = websocket1.receive_json()
		assert color1 not in data['data']['colors']
		assert color2 in data['data']['colors']
		with client.websocket_connect("/lobby/2") as websocket2:
			try:
				data1 = websocket1.receive_json()
				assert color1 not in data1['data']['colors']
				assert color2 not in data1['data']['colors']

				for player, expected, colors in zip(data['data']['players'], expectedPlayers, expected_colors):
					assert player['nickName'] == expected
					assert player['Color'] == colors

				data2 = websocket2.receive_json()
				assert color1 not in data2['data']['colors']
				assert color2 not in data2['data']['colors']
				assert data1 == data2

				for player, expected, colors in zip(data2['data']['players'], expectedPlayers, expected_colors):
					assert player['nickName'] == expected
					assert player['Color'] == colors

				new_color1 = int(random.choice(data1['data']['colors']))
				response = pickColor_put(player1id, new_color1, client)
				assert response.status_code == 200

				data = websocket1.receive_json()
				assert color1 in data['data']['colors']
				assert new_color1 not in data['data']['colors']

				data2 = websocket2.receive_json()
				assert new_color1 not in data2['data']['colors']
				assert color1 in data2['data']['colors']

				new_color2 = int(random.choice(data2['data']['colors']))
				response = pickColor_put(player2id, new_color2, client)
				assert response.status_code == 200

				data = websocket1.receive_json()
				assert color2 in data['data']['colors']
				assert new_color2 not in data['data']['colors']

				data2 = websocket2.receive_json()
				assert new_color2 not in data2['data']['colors']
				assert color2 in data2['data']['colors']

				websocket2.close()
				data = websocket1.receive_json()
				assert new_color2 in data['data']['colors']

				websocket1.close()
			except KeyboardInterrupt:
				websocket2.close()
				websocket1.close()

def test_taken_color():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	
	with client.websocket_connect("/lobby/1") as websocket1:
		expectedPlayers = create_players(1,game_id)
		expectedPlayers.insert(0,host)
		with db_session:
				player1 = db.Player.get(nickName=expectedPlayers[0])
				player2 = db.Player.get(nickName=expectedPlayers[1])
				player1id = player1.player_id
				player2id = player2.player_id
				color1, color2 = player1.color.color_id, player2.color.color_id
				expected_colors = [color1, color2]
		data = websocket1.receive_json()
		assert (color1 not in data['data']['colors'])
		assert (color2 in data['data']['colors'])
		with client.websocket_connect("/lobby/2") as websocket2:
			
			try:
				data1 = websocket1.receive_json()
				assert (color1 not in data1['data']['colors'])
				assert (color2 not in data1['data']['colors'])

				for player, expected, colors in zip(data['data']['players'], expectedPlayers, expected_colors):
					assert (player['nickName'] == expected)
					assert (player['Color'] == colors)

				data2 = websocket2.receive_json()
				assert (color1 not in data2['data']['colors'])
				assert (color2 not in data2['data']['colors'])
				assert (data1 == data2)

				for player, expected, colors in zip(data2['data']['players'], expectedPlayers, expected_colors):
					assert (player['nickName'] == expected)
					assert (player['Color'] == colors)

				new_color1 = color2
				response = pickColor_put(player1id, new_color1, client)
				assert (response.status_code == 400)

				websocket2.close()
				data = websocket1.receive_json()
				assert (color2 in data['data']['colors'])

				websocket1.close()
			except KeyboardInterrupt:
				websocket2.close()
				websocket1.close()