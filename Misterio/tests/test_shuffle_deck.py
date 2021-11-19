from fastapi.testclient import TestClient
from pony.orm import db_session
from Misterio.server import app
import Misterio.database as db
from Misterio.testing_utils import *

client = TestClient(app)

#make sure that no player gets an envelope card
def test_envelope():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1,lobby_id)
    expected_players.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected

            response = start_game_post(1, client)
            assert response.status_code == 200
            with db_session:
                playerCards = []
                lobby = db.Lobby.get(lobby_id=lobby_id)
                for player in expected_players:
                    playerCards.append(list(db.Player.get(nickname=player).cards))
                assert lobby.game.monster not in playerCards
                assert lobby.game.room not in playerCards
                assert lobby.game.victim not in playerCards
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()

#make sure that no player gets a duplicated cars
def test_duplication():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1,lobby_id)
    expected_players.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected

            response = start_game_post(1, client)
            assert response.status_code == 200
            with db_session:
                game = db.Lobby.get(lobby_id=lobby_id)
                cards1 = list(db.Player.get(nickname=host).cards)
                cards2 = list(db.Player.get(nickname=expected_players[1]).cards)
                for card in cards1:
                    assert card not in cards2
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()

def test_random_first():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1,lobby_id)
    expected_players.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected

            response = start_game_post(1, client)
            assert response.status_code == 200
            with db_session:
                first_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1,lobby_id)
    expected_players.insert(0,host)
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            data = websocket2.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected

            response = start_game_post(1, client)
            assert response.status_code == 200
            with db_session:
                second_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
            assert first_player != second_player
            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    