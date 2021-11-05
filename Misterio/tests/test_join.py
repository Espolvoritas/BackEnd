from fastapi.testclient import TestClient
from pony.orm import db_session, flush
import pytest
from fastapi import WebSocketDisconnect
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

def test_join():
    db.clear_tables()

    with db_session:
       
        player1 = db.Player(nickName="foo1")
        player2 = db.Player(nickName="foo2")
        player3 = db.Player(nickName="foo3")
        flush()
        
        game = db.Game(name="fooGame", host=player2, isStarted=False)
        flush()
        game.addPlayer(player1)
        flush()
        game.addPlayer(player2)
        flush()
        game.addPlayer(player3)
        flush()

        game_id = game.game_id
        taken_nickname = "foo2"
        free_nickname = "foo4"

    response1 = client.post("/lobby/joinCheck",
                        headers={"accept": "application/json", "Content-Type" : "application/json"},
                        json={"gameId": game_id, "playerNickname": taken_nickname})

    response2 = client.post("/lobby/joinCheck",
                        headers={"accept": "application/json", "Content-Type" : "application/json"},
                        json={"gameId": game_id, "playerNickname": free_nickname}).json()

    print(response1)
    print(response2)

    db.clear_tables()

    assert response1.status_code == 400
    assert(response2["nicknameIsValid"] == True)
