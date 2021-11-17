from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient
from pony.orm import db_session
import string    
import random # define the random module  
import pytest
from Misterio.testing_utils import *

from Misterio.server import app
import Misterio.database as db

client = TestClient(app)


def test_start_game_one_player():
    db.clear_tables()
    host = get_random_string(6)
    response = create_game_post(host, client)
    with db_session:
        host = db.Player.get(nickname=host)
    assert response.status_code == 201
    response = start_game_post(1, client)
    print(response)
    assert response.status_code == 405


def test_startGame_two_players():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert player["nickname"] == expected

            response = start_game_post(1, client)
            assert response.status_code == 200
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()

def test_startGame_not_host():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert player["nickname"] == expected

            response = start_game_post(2, client)
            assert response.status_code == 403
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close

def test_startGame_no_lobby():
    db.clear_tables()
    with db_session:
        hostName = get_random_string(6)
        host = db.Player(nickname=hostName)
    response = start_game_post(host.player_id, client)
    assert response.status_code == 400