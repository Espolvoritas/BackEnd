from fastapi.testclient import TestClient
from pony.orm import db_session, flush

from Misterio.server import app
import Misterio.database as db
from Misterio.testing_utils import get_random_string
client = TestClient(app)

def test_no_games():
    db.clear_tables()
    response = client.get("/lobby/availableGames")
    assert response.status_code == 204

def test_get_single_game():
    db.clear_tables()
    #Create a game
    with db_session:
        host_player = db.Player(nickname="IAmHost")
        flush()
        new_game = db.Lobby(name="game1", host=host_player, is_started=False)
        flush()
        new_game.add_player(host_player)
        gamejson = {}
        gamejson["name"] = new_game.name
        gamejson["id"] = new_game.lobby_id
        gamejson["players"] = int(new_game.player_count)
        gamejson["host"] = new_game.host.nickname
        gamejson["password"] = False
    response = client.get("/lobby/availableGames")

    #Check response
    assert response.status_code == 200
    assert response.json() == [gamejson]
    

def test_various_games():
    db.clear_tables()
    with db_session:
        hosts = []
        for i in range(6):
            hostname=f"IAmHost{i}"
            host_player = db.Player(nickname=hostname)
            hosts.append(host_player)
        flush()
        games = []
        
        #Create games and join hosts
        for i in range(6):
            gamename=f"game{i}"
            game = db.Lobby(name=gamename, host=hosts[i], is_started=False)
            game.add_player(hosts[i])
            games.append(game)
        flush()

        #Create random players 
        players = []
        for i in range(24):
            player = db.Player(nickname=get_random_string(7))
            players.append(player)
        flush()
        
        #Add players to games
        prev = 0
        n = 0
        for i in range(6):
            for j in range(4):
                n = prev
                games[i].add_player(players[n])
                n += 1
                prev = n
        flush()
        gamesjson = []
        for i in range(6):
            gamejson = {}
            g = games[i]
            gamejson["name"] = g.name
            gamejson["id"] = g.lobby_id
            gamejson["players"] = int(g.player_count)
            gamejson["host"] = g.host.nickname
            gamejson["password"] = False
            gamesjson.append(gamejson)
        flush()

    response = client.get("/lobby/availableGames")
    assert response.status_code == 200
    assert response.json() == gamesjson

def test_full_games():
    db.clear_tables()
    with db_session:
        hosts = []
        for i in range(6):
            hostname=f"IAmHost{i}"
            host_player = db.Player(nickname=hostname)
            hosts.append(host_player)
        flush()
        games = []
        
        #Create games and join hosts
        for i in range(6):
            gamename=f"game{i}"
            game = db.Lobby(name=gamename, host=hosts[i], is_started=False)
            game.add_player(hosts[i])
            games.append(game)
        flush()

        #Create random players 
        players = []
        for i in range(30):
            player = db.Player(nickname=get_random_string(7))
            players.append(player)
        flush()
        
        #Add players to games
        prev = 0
        n = 0
        for i in range(6):
            for j in range(5):
                n = prev
                games[i].add_player(players[n])
                n += 1
                prev = n
        flush()
    response = client.get("/lobby/availableGames")
    assert response.status_code == 204
    

def test_full_and_available():
    db.clear_tables()
    with db_session:
        hosts = []
        for i in range(6):
            hostname=f"IAmHost{i}"
            host_player = db.Player(nickname=hostname)
            hosts.append(host_player)
        flush()
        games = []
        
        #Create games and join hosts
        for i in range(6):
            gamename=f"game{i}"
            game = db.Lobby(name=gamename, host=hosts[i], is_started=False)
            game.add_player(hosts[i])
            games.append(game)
        flush()

        #Create random players 
        players = []
        for i in range(30):
            player = db.Player(nickname=get_random_string(7))
            players.append(player)
        flush()
        
        #Add players to games
        prev = 0
        n = 0
        for i in range(4):
            for j in range(5):
                n = prev
                games[i].add_player(players[n])
                n += 1
                prev = n
        flush()
        gamesjson = []
        for i in range(4,6):
            gamejson = {}
            g = games[i]
            gamejson["name"] = g.name
            gamejson["id"] = g.lobby_id
            gamejson["players"] = int(g.player_count)
            gamejson["host"] = g.host.nickname
            gamejson["password"] = False
            gamesjson.append(gamejson)
    response = client.get("/lobby/availableGames")
    assert response.status_code == 200
    assert response.json() == gamesjson
