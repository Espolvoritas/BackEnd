from fastapi.testclient import TestClient
from pony.orm import db_session
import pytest
from fastapi import WebSocketDisconnect
from Misterio.testing_utils import *
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
            for player in data["players"]:
                assert player["nickname"] == host
                with pytest.raises(WebSocketDisconnect, match="1008"):
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
            for player in data["players"]:
                assert player["nickname"] == host
            with pytest.raises(WebSocketDisconnect, match="1008"):
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
            for player in data["players"]:
                assert player["nickname"] == host1
            data = websocket2.receive_json()
            for player in data["players"]:
                assert player["nickname"] == host2
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
            for player in data["players"]:
                assert player["nickname"] == host
            with pytest.raises(WebSocketDisconnect, match="1008"):
                with client.websocket_connect("/lobby/1") as websocket2:
                    raise WebSocketDisconnect(1000)
            websocket1.close()
        except KeyboardInterrupt:
            websocket1.close()

def test_leave_host():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        pytest.raises(WebSocketDisconnect, match="1001"):
        with client.websocket_connect("/lobby/2") as websocket2:
            try:
                data = websocket1.receive_json()
                for player, expected in zip(data["players"], expectedPlayers):
                    assert player["nickname"] == expected
                data = websocket2.receive_json()

                for player, expected in zip(data["players"], expectedPlayers):
                    assert player["nickname"] == expected
                websocket1.close()
                data = websocket2.receive_json()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_get_two_players():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expected_players):
                print(player)
                assert player["nickname"] == expected
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()