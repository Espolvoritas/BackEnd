from fastapi.testclient import TestClient
from pony.orm import db_session
from typing import Match
import pytest
from fastapi import WebSocketDisconnect
from Misterio.functions import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)


def test_no_lobby():
	db.clear_tables()
	host = get_random_string(6)
	game = create_game_post(host, client)
	
	with client.websocket_connect("/lobby/1") as websocket1:
		try:
			data = websocket1.receive_json()
			for player in data['data']['players']:
				assert player['nickName'] == host
				with pytest.raises(WebSocketDisconnect, match='1008'):
					with client.websocket_connect("/lobby/2"):
						raise WebSocketDisconnect(1000)
		except KeyboardInterrupt:
			websocket1.close()

def test_invalid_player():
	db.clear_tables()
	host = get_random_string(6)
	game = create_game_post(host, client)
	with client.websocket_connect("/lobby/1") as websocket1:
		try:
			data = websocket1.receive_json()
			for player in data['data']['players']:
				assert player['nickName'] == host
			with pytest.raises(WebSocketDisconnect, match='1008'):
				with client.websocket_connect("/lobby/2"):
					raise WebSocketDisconnect(1000)
		except KeyboardInterrupt:
			websocket1.close()

def test_two_lobbys():
	db.clear_tables()
	host1 = get_random_string(6)
	game1 = create_game_post(host1, client)
	host2 = get_random_string(6)
	game2 = create_game_post(host2, client)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player in data['data']['players']:
				assert player['nickName'] == host1
			data = websocket2.receive_json()
			for player in data['data']['players']:
				assert player['nickName'] == host2
			websocket2.close()
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

def test_duplicate():
	db.clear_tables()
	host = get_random_string(6)
	game = create_game_post(host, client)
	with client.websocket_connect("/lobby/1") as websocket1:
		try:
			data = websocket1.receive_json()
			for player in data['data']['players']:
				assert player['nickName'] == host
			with pytest.raises(WebSocketDisconnect, match='1008'):
				with client.websocket_connect("/lobby/1") as websocket2:
					raise WebSocketDisconnect(1000)
			websocket1.close()
		except KeyboardInterrupt:
			websocket1.close()

def test_leave_host():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1, game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		pytest.raises(WebSocketDisconnect, match='1001'):
		with client.websocket_connect("/lobby/2") as websocket2:
			try:
				data = websocket1.receive_json()
				for player, expected in zip(data['data']['players'], expectedPlayers):
					assert player['nickName'] == expected
				data = websocket2.receive_json()

				for player, expected in zip(data['data']['players'], expectedPlayers):
					assert player['nickName'] == expected
				websocket1.close()
				data = websocket2.receive_json()
				websocket2.close()
			except KeyboardInterrupt:
				websocket2.close()
				websocket1.close()

def test_get_two_players():
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
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['data']['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()