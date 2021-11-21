from fastapi.testclient import TestClient
from pony.orm import db_session
import logging
from Misterio.testing_utils import *
from Misterio.server import app
from Misterio.functions import get_cell_by_coordinates
import Misterio.database as db

client = TestClient(app)
logger = logging.getLogger("gameboard")

###
#IMPORTANT INFO
#Due to some misunderstandings y and x are inverted between frontend and backend
#So, backend's x dimension is frontend's y. As such, they are inverted in the code, backend send y,x and receives x,y
#As such, in this tests we need to invert it again and check for and send y,x
###
@db_session
def find_entrance(movement):
    for possibility in movement:
        # don't ask
        cell = get_cell_by_coordinates(possibility["y"], possibility["x"])
        if "ENTRANCE-" in cell.cell_type :
            return possibility

@db_session
def find_room(movement):
    for possibility in movement:
        # don't ask
        cell = get_cell_by_coordinates(possibility["y"], possibility["x"])
        if "ROOM" == cell.cell_type :
            return possibility

@db_session
def find_trap(movement):
    for possibility in movement:
        # don't ask
        cell = get_cell_by_coordinates(possibility["y"], possibility["x"])
        if "TRAP" == cell.cell_type :
            return possibility

@db_session
def find_portal(movement):
    for possibility in movement:
        # don't ask
        cell = get_cell_by_coordinates(possibility["y"], possibility["x"])
        if "PORTAL-" in cell.cell_type :
            return possibility

def test_bad_move():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, "", client).json()["lobby_id"]
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
    lobby_id = create_game_post(host, "", client).json()["lobby_id"]
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
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = random.choice(possible_moves)
                response = move_post(current_player.player_id, movement["x"], movement["y"], movement["remaining"],client)
                assert response.status_code == 200
                data = websocket1.receive_json()
                data = websocket2.receive_json()
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_pass_turn():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    roll = 1
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = random.choice(possible_moves)
                response = move_post(current_player.player_id, movement["x"], movement["y"], 0,client)
                assert response.status_code == 200
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    assert current_player.player_id == next_player.player_id
                data = websocket1.receive_json()
                data = websocket2.receive_json()
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_room_move():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    roll = 6
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = find_entrance(possible_moves)
                response = move_post(current_player.player_id, movement["y"], movement["x"], movement["remaining"],client)
                assert response.status_code == 200
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    entrance = current_player.location.cell_type.split("ENTRANCE-")
                movement= find_room(response.json()["moves"])
                response = move_post(current_player.player_id, movement["y"], movement["x"], movement["remaining"],client)
                assert response.status_code == 200
                #turn hasn't changed because we are in a room
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    assert current_player.location.cell_type == "ROOM"
                    assert entrance[1]==current_player.location.room_name
                data = websocket1.receive_json()
                data = websocket2.receive_json()
                websocket2.close()
                data = websocket1.receive_json()
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

# COMBUSTIBLE LEMONS
def test_portal():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    roll = 6
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = find_portal(possible_moves)
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                assert response.status_code == 200
                with db_session:
                    entrance = get_cell_by_coordinates(movement["y"], movement["x"])
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    assert current_player.player_id == next_player.player_id
                response = roll_dice_post(current_player.player_id, 1, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = random.choice(possible_moves)
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                response = roll_dice_post(current_player.player_id, 1, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = find_portal(possible_moves)
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    exit = get_cell_by_coordinates(movement["y"], movement["x"])
                    assert entrance.cell_type == exit.cell_type
                    assert entrance.x != exit.x or entrance.y != exit.y
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                assert response.status_code == 200
                websocket2.close()
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_trap():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

    roll = 6
    with db_session:
        current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
        current_player_nickName = current_player.nickname
        next_player = current_player.next_player

    with client.websocket_connect("/gameBoard/" + str(current_player.player_id)) as websocket1:
        data = websocket1.receive_json()
        with client.websocket_connect("/gameBoard/" + str(next_player.player_id)) as websocket2:
            data = websocket2.receive_json()
            try:
                assert current_player_nickName == data["current_player"]
                response = roll_dice_post(current_player.player_id, roll, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = find_trap(possible_moves)
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                assert response.status_code == 200
                with db_session:
                    entrance = get_cell_by_coordinates(movement["y"], movement["x"])
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    assert current_player.player_id == next_player.player_id
                response = roll_dice_post(current_player.player_id, 1, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = random.choice(possible_moves)
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    assert current_player.player_id == next_player.player_id
                response = roll_dice_post(current_player.player_id, 1, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = random.choice(possible_moves)
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                response = roll_dice_post(current_player.player_id, 1, client)
                assert (response.status_code == 200)
                possible_moves = response.json()["moves"]
                movement = find_trap(possible_moves)
                with db_session:
                    current_player = db.Lobby.get(lobby_id=lobby_id).game.current_player
                    exit = get_cell_by_coordinates(movement["y"], movement["x"])
                    assert entrance.cell_type == exit.cell_type
                    assert entrance.x != exit.x or entrance.y != exit.y
                response = move_post(current_player.player_id, movement["y"], movement["x"], 0,client)
                assert response.status_code == 200
                websocket2.close()
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()