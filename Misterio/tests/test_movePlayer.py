from fastapi.testclient import TestClient
from pony.orm import db_session, flush
import string
import logging
import random
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)
logger = logging.getLogger("gameboard")

@db_session
def find_entrance(movement):
    for possibility in movement:
        cell = cellByCoordinates(possibility["x"], possibility["y"])
        if "ENTRANCE-" in cell.cell_type :
            return possibility

@db_session
def find_room(movement):
    for possibility in movement:
        cell = cellByCoordinates(possibility["x"], possibility["y"])
        print(cell)
        if "ROOM" == cell.cell_type :
            return possibility

def test_bad_move():
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

        roll = random.randint(1,6)
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                response = move_post(current_player.player_id, 999, 999, 0,client)
                assert response.status_code == 400
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
                websocket1.close()

def test_move():
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

        roll = random.randint(1,6)
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                print("RESPONSE: ",response.json())
                possible_moves = response.json()["moves"]
                movement = random.choice(possible_moves)
                response = move_post(current_player.player_id, movement["x"], movement["y"], movement["remaining"],client)
                assert response.status_code == 200
                print(response)
                data = websocket1.receive_json()
                print(data)
                data = websocket2.receive_json()
                print("Move broadcast", data)
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()