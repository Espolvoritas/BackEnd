from typing import Match
from server import app
from fastapi.testclient import TestClient
import string
import pytest
import asyncio
from fastapi import WebSocketDisconnect
import database as db
from pony.orm import db_session, flush, select
import random # define the random module  

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

def test_no_lobby():
	clear_tables()
	host = get_random_string(6)
	create_new_game(host)
	with db_session:
		player = db.Player(nickName=get_random_string(6))
	with client.websocket_connect("/game/getPlayers/1") as websocket1:
		try:
			data = websocket1.receive_json()
			for player in data:
				assert player == host
				with pytest.raises(WebSocketDisconnect, match='1008'):
					with client.websocket_connect("/game/getPlayers/2"):
						raise WebSocketDisconnect(1000)
		except KeyboardInterrupt:
			websocket1.close()

def test_invalid_player():
	clear_tables()
	host = get_random_string(6)
	create_new_game(host)	
	with client.websocket_connect("/game/getPlayers/1") as websocket1:
		try:
			data = websocket1.receive_json()
			for player in data:
				assert player == host
			with pytest.raises(WebSocketDisconnect, match='1008'):
				with client.websocket_connect("/game/getPlayers/2"):
					raise WebSocketDisconnect(1000)
		except KeyboardInterrupt:
			websocket1.close()

def test_two_lobbys():
	clear_tables()
	host1 = get_random_string(6)
	create_new_game(host1)
	host2 = get_random_string(6)
	create_new_game(host2)
	with client.websocket_connect("/game/getPlayers/1") as websocket1, \
		client.websocket_connect("/game/getPlayers/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player in data:
				assert player == host1
			data = websocket2.receive_json()
			for player in data:
				assert player == host2
			websocket2.close()
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

def test_no_lobby():
	clear_tables()
	host = get_random_string(6)
	create_new_game(host)
	with client.websocket_connect("/game/getPlayers/1") as websocket1:
		try:
			data = websocket1.receive_json()
			for player in data:
				assert player == host
			with pytest.raises(WebSocketDisconnect, match='1008'):
				with client.websocket_connect("game/getPlayers/1") as websocket2:
					raise WebSocketDisconnect(1000)
			websocket1.close()
		except KeyboardInterrupt:
			websocket1.close()

def test_get_two_players():
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
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data, expectedPlayers):
				assert player == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()