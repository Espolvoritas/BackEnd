from fastapi.testclient import TestClient
from pony.orm import db_session, select
from Misterio.functions import get_lobby_by_id
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db
import base64 
client = TestClient(app)

def test_valid_password():
    db.clear_tables()
    host = get_random_string(6)
    password = "somepassword".encode("ascii")
    password = base64.b64encode(password)
    lobby_id = create_game_post(host, password, client).json()["lobby_id"]
    expected_players = [host]
    response = join_game_post(lobby_id, get_random_string(6), "somepassword", client)
    print(response.json())
    assert (response.status_code == 200)
    assert (response.json()["nickname_is_valid"])
    assert (response.json()["password_is_valid"])

def test_invalid_password():
    db.clear_tables()
    host = get_random_string(6)
    password = "somepassword".encode("ascii")
    password = base64.b64encode(password)
    lobby_id = create_game_post(host, password, client).json()["lobby_id"]
    expected_players = [host]
    response = join_game_post(lobby_id, get_random_string(6), "incorrectpassword", client)
    print(response.json())
    assert (response.status_code == 401)

    response = join_game_post(lobby_id, get_random_string(6), "", client)
    print(response.json())
    assert (response.status_code == 401)

