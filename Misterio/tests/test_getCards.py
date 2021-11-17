from fastapi.testclient import TestClient
from pony.orm import db_session
import string
import random # define the random module  

from Misterio.server import app
import Misterio.database as db
from Misterio.testing_utils import *

client = TestClient(app)

#make sure that no player gets an envelope card
def test_envelope():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1,lobby_id)
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
    with client.websocket_connect("/gameBoard/1") as websocket1, \
        client.websocket_connect("/gameBoard/2") as websocket2:
        try:
            data1 = websocket1.receive_json()
            data2 = websocket2.receive_json()
            with db_session:
                game = db.Lobby.get(lobby_id=lobby_id).game
                assert game.victim not in data1["cards"] and game.victim not in data2["cards"]
                assert game.room not in data1["cards"] and game.room not in data2["cards"]
                assert game.monster not in data1["cards"] and game.monster not in data2["cards"]
            websocket2.close()
            websocket1.close()
        except KeyboardInterrupt:
            websocket1.close()
    

#make sure that no player gets an envelope card
def test_no_duplication():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1,lobby_id)
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
    with client.websocket_connect("/gameBoard/1") as websocket1, \
        client.websocket_connect("/gameBoard/2") as websocket2:
        try:
            data1 = websocket1.receive_json()
            data2 = websocket2.receive_json()
            for card in data1["cards"]:
                assert card not in data2["cards"]
            websocket2.close()
            websocket1.close()
        except KeyboardInterrupt:
            websocket1.close()