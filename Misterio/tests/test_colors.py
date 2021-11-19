from fastapi.testclient import TestClient
from pony.orm import db_session
import random # define the random module  
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

def test_join_colors():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1,lobby_id)
    expected_players.insert(0,host)

    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            with db_session:
                player1 = db.Player.get(nickname=expected_players[0])
                player2 = db.Player.get(nickname=expected_players[1])

                color1, color2 = player1.color, player2.color

            assert color1 is not None
            assert color2 is not None
            
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
                assert player["Color"] not in data["colors"]

            data2 = websocket2.receive_json()
            for player, expected in zip(data2["players"], expected_players):
                assert player["nickname"] == expected
                assert player["Color"] not in data2["colors"]

            
            websocket2.close()
            assert color2.color_id not in data["colors"]

            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expected_players):
                assert player["nickname"] == expected
                assert player["Color"] not in data["colors"]
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    db.clear_tables()

def test_change_color():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    
    with client.websocket_connect("/lobby/1") as websocket1:
        expected_players = create_players(1,lobby_id)
        expected_players.insert(0,host)
        with db_session:
            player1 = db.Player.get(nickname=expected_players[0])
            player2 = db.Player.get(nickname=expected_players[1])
            player1id = player1.player_id
            player2id = player2.player_id
            color1, color2 = player1.color.color_id, player2.color.color_id
            expected_colors = [color1, color2]
        data = websocket1.receive_json()
        assert color1 not in data["colors"]
        assert color2 in data["colors"]
        with client.websocket_connect("/lobby/2") as websocket2:
            try:
                data1 = websocket1.receive_json()
                assert color1 not in data1["colors"]
                assert color2 not in data1["colors"]

                for player, expected, colors in zip(data["players"], expected_players, expected_colors):
                    assert player["nickname"] == expected
                    assert player["Color"] == colors

                data2 = websocket2.receive_json()
                assert color1 not in data2["colors"]
                assert color2 not in data2["colors"]
                assert data1 == data2

                for player, expected, colors in zip(data2["players"], expected_players, expected_colors):
                    assert player["nickname"] == expected
                    assert player["Color"] == colors

                new_color1 = int(random.choice(data1["colors"]))
                response = pick_color_put(player1id, new_color1, client)
                assert response.status_code == 200

                data = websocket1.receive_json()
                assert color1 in data["colors"]
                assert new_color1 not in data["colors"]

                data2 = websocket2.receive_json()
                assert new_color1 not in data2["colors"]
                assert color1 in data2["colors"]

                new_color2 = int(random.choice(data2["colors"]))
                response = pick_color_put(player2id, new_color2, client)
                assert response.status_code == 200

                data = websocket1.receive_json()
                assert color2 in data["colors"]
                assert new_color2 not in data["colors"]

                data2 = websocket2.receive_json()
                assert new_color2 not in data2["colors"]
                assert color2 in data2["colors"]

                websocket2.close()
                data = websocket1.receive_json()
                assert new_color2 in data["colors"]

                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_taken_color():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    
    with client.websocket_connect("/lobby/1") as websocket1:
        expected_players = create_players(1,lobby_id)
        expected_players.insert(0,host)
        with db_session:
                player1 = db.Player.get(nickname=expected_players[0])
                player2 = db.Player.get(nickname=expected_players[1])
                player1id = player1.player_id
                player2id = player2.player_id
                color1, color2 = player1.color.color_id, player2.color.color_id
                expected_colors = [color1, color2]
        data = websocket1.receive_json()
        assert (color1 not in data["colors"])
        assert (color2 in data["colors"])
        with client.websocket_connect("/lobby/2") as websocket2:
            
            try:
                data1 = websocket1.receive_json()
                assert (color1 not in data1["colors"])
                assert (color2 not in data1["colors"])

                for player, expected, colors in zip(data["players"], expected_players, expected_colors):
                    assert (player["nickname"] == expected)
                    assert (player["Color"] == colors)

                data2 = websocket2.receive_json()
                assert (color1 not in data2["colors"])
                assert (color2 not in data2["colors"])
                assert (data1 == data2)

                for player, expected, colors in zip(data2["players"], expected_players, expected_colors):
                    assert (player["nickname"] == expected)
                    assert (player["Color"] == colors)

                new_color1 = color2
                response = pick_color_put(player1id, new_color1, client)
                assert (response.status_code == 400)

                websocket2.close()
                data = websocket1.receive_json()
                assert (color2 in data["colors"])

                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()