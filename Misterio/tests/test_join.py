from fastapi.testclient import TestClient
from pony.orm import db_session, flush
from Misterio.server import app
import Misterio.database as db
from Misterio.testing_utils import join_game_post
client = TestClient(app)

def test_join():
    db.clear_tables()

    with db_session:
       
        player1 = db.Player(nickname="foo1")
        player2 = db.Player(nickname="foo2")
        player3 = db.Player(nickname="foo3")
        flush()
        
        game = db.Lobby(name="fooGame", host=player2, is_started=False)
        flush()
        game.add_player(player1)
        flush()
        game.add_player(player2)
        flush()
        game.add_player(player3)
        flush()

        lobby_id = game.lobby_id
        taken_nickname = "foo2"
        free_nickname = "foo4"

    response1 = join_game_post(lobby_id, taken_nickname, "", client)
    
    response2 = join_game_post(lobby_id, free_nickname, "", client)
    
    print(response1.json())
    print(response2.json())

    db.clear_tables()

    assert response1.status_code == 400
    assert(response2.json()["nickname_is_valid"] == True)
