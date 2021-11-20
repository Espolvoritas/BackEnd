from fastapi.testclient import TestClient
from pony.orm import db_session, select
from Misterio.functions import get_lobby_by_id
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

def test_card_usage_2_players():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        lobby = get_lobby_by_id(lobby_id)
        salem_card = select(c for c in db.Card if c.card_type == "SALEM").first()
        player1 = select(p for p in db.Player if salem_card in p.cards).first()
        envelope = [lobby.game.monster.card_id, lobby.game.victim.card_id, lobby.game.room.card_id]
        player2 = player1.next_player.player_id
        player1 = player1.player_id
        curr_player_id = lobby.game.current_player.player_id

    with client.websocket_connect("/gameBoard/" + str(player1)) as websocket1:
        websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(player2)) as websocket2:
            websocket2.receive_json()#connection broadcast
            try:
                if (curr_player_id == player1):
                    response = salem_post(player1, "MONSTER", client)
                    print(response.json())
                    data = websocket2.receive_json()
                    assert (data["code"] & 2048)
                    assert (data["card_type_revealed"] == "MONSTER")
                    assert (response.status_code == 200)
                    assert (response.json()["envelope_card"] in envelope)

                else:
                    response = salem_post(player2, "VICTIM", client)
                    print(response.json())
                    data = websocket1.receive_json()
                    assert (data["code"] & 2048)
                    assert (data["card_type_revealed"] == "VICTIM")
                    assert (response.status_code == 200)
                    assert (response.json()["envelope_card"] in envelope)

                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()
        
        with db_session:
            salem_card = select(c for c in db.Card if c.card_type == "SALEM").first()
            player = db.Lobby.get(lobby_id=lobby_id).game.current_player
            assert(salem_card not in player.cards)

def test_no_card():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        lobby = get_lobby_by_id(lobby_id)
        salem_card = select(c for c in db.Card if c.card_type == "SALEM").first()
        player1 = select(p for p in db.Player if salem_card in p.cards).first()
        player1.cards.remove(salem_card)
        player2 = player1.next_player.player_id
        player1 = player1.player_id
        curr_player_id = lobby.game.current_player.player_id

    with client.websocket_connect("/gameBoard/" + str(player1)) as websocket1:
        websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(player2)) as websocket2:
            websocket2.receive_json()#connection broadcast
            try:
                if (curr_player_id == player1):
                    response = salem_post(player1, "ROOM", client)
                    print(response.json())
                    assert (response.status_code == 403)

                else:
                    response = salem_post(player2, "ROOM", client)
                    print(response.json())
                    assert (response.status_code == 403)
                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_not_turn():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    with db_session:
        lobby = get_lobby_by_id(lobby_id)
        salem_card = select(c for c in db.Card if c.card_type == "SALEM").first()
        player1 = select(p for p in db.Player if salem_card in p.cards).first()
        player2 = player1.next_player.player_id
        player1 = player1.player_id
        curr_player_id = lobby.game.current_player.player_id

    with client.websocket_connect("/gameBoard/" + str(player1)) as websocket1:
        websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(player2)) as websocket2:
            websocket2.receive_json()#connection broadcast
            try:
                if (curr_player_id == player1):
                    response = salem_post(player2, "ROOM", client)
                    print(response.json())
                    assert (response.status_code == 403)

                else:
                    response = salem_post(player1, "ROOM", client)
                    print(response.json())
                    assert (response.status_code == 403)
                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()