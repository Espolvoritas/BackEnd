from server import app
from fastapi.testclient import TestClient

import database
from database import db
from pony.orm import db_session, flush

client = TestClient(app)

def clear_tables():
    db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.create_tables()

def test_join():
    clear_tables()

    with db_session:
       
        player1 = database.Player(nickName="foo1")
        player2 = database.Player(nickName="foo2")
        player3 = database.Player(nickName="foo3")
        flush()
        
        game = database.Game(name="fooGame", host=player2, isStarted=False)
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

    response1 = client.post("/game/joinCheck",
                        headers={"accept": "application/json", "Content-Type" : "application/json"},
                        json={"gameId": game_id, "playerNickname": taken_nickname}).json()

    response2 = client.post("/game/joinCheck",
                        headers={"accept": "application/json", "Content-Type" : "application/json"},
                        json={"gameId": game_id, "playerNickname": free_nickname}).json()

    print(response1)
    print(response2)

    clear_tables()

    assert(response1["nicknameIsValid"] == False)
    assert(response2["nicknameIsValid"] == True)
