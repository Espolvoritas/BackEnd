from fastapi.testclient import TestClient
from pony.orm import db_session
import logging
import random
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)
logger = logging.getLogger("gameboard")

def test_send_one_roll():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)
    
    roll = random.randint(1,6)
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    print(current_player)
    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        print(data)
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            print(data)
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                #assert next_player == data["current_player"]
                websocket2.close()
                data = websocket1.receive_json()
                print(data)
                websocket1.close()
            except KeyboardInterrupt:
                websocket1.close()

    with db_session:
        player = db.Player.get(player_id=current_player.player_id)
        curr_roll = player.current_dice_roll
    assert curr_roll == roll

def test_send_one_roll_not_in_turn():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)

    connect_and_start_game_2_players(expected_players, client)
    
    roll = random.randint(1,6)
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        print(data)
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            print(data)
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(next_player.player_id, roll, client)
                assert (response.status_code == 403)
                websocket2.close()
                data = websocket1.receive_json()
                print(data)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()


    with db_session:
        player = db.Player.get(player_id=current_player.player_id)
        #if current player is player 2
        assert player.current_dice_roll == 0