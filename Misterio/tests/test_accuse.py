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

def test_right_accusation():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        lobby = db.Lobby.get(lobby_id=lobby_id)
        current_player = lobby.game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player
        room = lobby.game.room.card_id
        monster = lobby.game.monster.card_id
        victim = lobby.game.victim.card_id

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                accuse_post(current_player.player_id,room, monster, victim, client)
                data = websocket1.receive_json()
                assert data["data"]["won"] == True
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
                websocket1.close()

def test_wrong_accusation():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        lobby = db.Lobby.get(lobby_id=lobby_id)
        current_player = lobby.game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player
        room = lobby.game.room.card_id
        monster = lobby.game.monster.card_id
        victim = lobby.game.victim.card_id

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                accuse_post(current_player.player_id,room, (monster-1), victim, client)
                data = websocket1.receive_json()
                assert data["data"]["won"] == False
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
<<<<<<< HEAD
                websocket1.close()
=======
                websocket1.close()
>>>>>>> 0203b2d... Consistence in coding-style
