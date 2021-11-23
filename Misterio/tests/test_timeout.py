from fastapi.testclient import TestClient
from pony.orm import db_session
import logging
from time import sleep

from Misterio.constants import DISCONNECT_TIMER
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)
logger = logging.getLogger("gameboard")

def test_reconnect():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, "", client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    roll = random.randint(1,6)
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        next_player = current_player.next_player
        next_player_nickName = next_player.nickname

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            data = websocket2.receive_json()
            websocket2.close()
            sleep(DISCONNECT_TIMER)
        data = websocket1.receive_json()
        assert data['msg']['str'] == ("El jugador " + str(next_player_nickName) + " se desconectó")
        assert data['msg']['user'] == "Sistema"
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            websocket2.close()
            websocket1.close()

def test_lose_turn():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, "", client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            data = websocket2.receive_json()
            websocket2.close()
            sleep(DISCONNECT_TIMER)
        data = websocket1.receive_json()
        assert data['msg']['str'] == ("El jugador " + str(current_player_nickName) + " se desconectó")
        assert data['msg']['user'] == "Sistema"
        with db_session:
            assert db.Lobby.get(lobby_id=lobby_id).game.current_player != current_player
        with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            websocket2.close()
            websocket1.close()

def test_yield_turn():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, "", client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player
        next_player_nickName = current_player.next_player.nickname

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            #data = websocket1.receive_json()
            yield_turn_post(current_player.player_id,client)
            data = websocket1.receive_json()
            assert data['current_player'] == next_player_nickName
            data = websocket1.receive_json()
            assert data['msg']['str'] == ("El jugador " + str(current_player_nickName) + " se quedo sin tiempo y perdio el turno")
            assert data['msg']['user'] == "Sistema"
            with db_session:
                assert db.Lobby.get(lobby_id=lobby_id).game.current_player != current_player
            