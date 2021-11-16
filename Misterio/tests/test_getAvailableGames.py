from fastapi.testclient import TestClient
from pony.orm import db_session, flush
import string    
import random # define the random module  

from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str

def test_no_games():
    db.clear_tables()
    response = client.get("/lobby/availableGames")
    assert response.status_code == 204

def test_get_single_game():
    db.clear_tables()
    #Create a game
    with db_session:
        hostPlayer = db.Player(nickname="IAmHost")
        flush()
        newGame = db.Lobby(name="game1", host=hostPlayer, is_started=False)
        flush()
        newGame.add_player(hostPlayer)
        gamejson = {}
        gamejson["name"] = newGame.name
        gamejson["id"] = newGame.lobby_id
        gamejson["players"] = int(newGame.player_count)
        gamejson["host"] = newGame.host.nickname
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
            hostPlayer = db.Player(nickname=hostname)
            hosts.append(hostPlayer)
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
            hostPlayer = db.Player(nickname=hostname)
            hosts.append(hostPlayer)
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
            hostPlayer = db.Player(nickname=hostname)
            hosts.append(hostPlayer)
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
