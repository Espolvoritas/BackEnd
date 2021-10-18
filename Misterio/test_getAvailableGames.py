from server import app
from fastapi.testclient import TestClient
from pony.orm import db_session, flush
import string    
import random # define the random module  
import database as db

client = TestClient(app)

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    
    db.db.create_tables()


def test_no_games():
    response = client.get("/game/availableGames")
    assert response.status_code == 204    

def test_get_single_game():
    #Create a game
    with db_session:
        hostPlayer = db.Player(nickName="IAmHost")
        flush()
        newGame = db.Game(name="game1", host=hostPlayer, isStarted=False)
        newGame.addPlayer(hostPlayer)

    response = client.get("/game/availableGames")

    #Check response
    assert response.status_code == 200
    assert response.json() == {'totalGames': 1, 'games': [{'name': 'game1', 'players': 1, 'host': 'IAmHost', 'password': False}]}
    clear_tables()

def test_various_games():
    with db_session:
        hosts = []
        for i in range(6):
            hostname=f"IAmHost{i}"
            hostPlayer = db.Player(nickName=hostname)
            hosts.append(hostPlayer)
        flush()
        games = []
        
        #Create games and join hosts
        for i in range(6):
            gamename=f"game{i}"
            game = db.Game(name=gamename, host=hosts[i], isStarted=False)
            game.addPlayer(hosts[i])
            games.append(game)
        flush()

        #Create random players 
        players = []
        for i in range(24):
            player = db.Player(nickName=get_random_string(7))
            players.append(player)
        flush()
        
        #Add players to games
        prev = 0
        n = 0
        for i in range(6):
            for j in range(4):
                n = prev
                games[i].addPlayer(players[n])
                n += 1
                prev = n
        flush()
        gamesjson = []
        for i in range(6):
            gamejson = {}
            g = games[i]
            gamejson['name'] = g.name
            gamejson['players'] = int(g.playerCount)
            gamejson['host'] = g.host.nickName
            gamejson['password'] = False
            gamesjson.append(gamejson)
        flush()

    response = client.get("/game/availableGames")
    testjson = {"totalGames":6, "games":gamesjson}    
    assert response.status_code == 200
    assert response.json() == testjson
    clear_tables()

def test_full_games():
    with db_session:
        hosts = []
        for i in range(6):
            hostname=f"IAmHost{i}"
            hostPlayer = db.Player(nickName=hostname)
            hosts.append(hostPlayer)
        flush()
        games = []
        
        #Create games and join hosts
        for i in range(6):
            gamename=f"game{i}"
            game = db.Game(name=gamename, host=hosts[i], isStarted=False)
            game.addPlayer(hosts[i])
            games.append(game)
        flush()

        #Create random players 
        players = []
        for i in range(30):
            player = db.Player(nickName=get_random_string(7))
            players.append(player)
        flush()
        
        #Add players to games
        prev = 0
        n = 0
        for i in range(6):
            for j in range(5):
                n = prev
                games[i].addPlayer(players[n])
                n += 1
                prev = n
        flush()
    response = client.get("/game/availableGames")
    testjson = {"totalGames":0, "games":[]}    
    assert response.status_code == 204
    assert response.json() == testjson
    clear_tables()

def test_full_and_available():
    with db_session:
        hosts = []
        for i in range(6):
            hostname=f"IAmHost{i}"
            hostPlayer = db.Player(nickName=hostname)
            hosts.append(hostPlayer)
        flush()
        games = []
        
        #Create games and join hosts
        for i in range(6):
            gamename=f"game{i}"
            game = db.Game(name=gamename, host=hosts[i], isStarted=False)
            game.addPlayer(hosts[i])
            games.append(game)
        flush()

        #Create random players 
        players = []
        for i in range(30):
            player = db.Player(nickName=get_random_string(7))
            players.append(player)
        flush()
        
        #Add players to games
        prev = 0
        n = 0
        for i in range(4):
            for j in range(5):
                n = prev
                games[i].addPlayer(players[n])
                n += 1
                prev = n
        flush()
        gamesjson = []
        for i in range(4,6):
            gamejson = {}
            g = games[i]
            gamejson['name'] = g.name
            game['id'] = g.game_id
            gamejson['players'] = int(g.playerCount)
            gamejson['host'] = g.host.nickName
            gamejson['password'] = False
            gamesjson.append(gamejson)
    response = client.get("/game/availableGames")
    testjson = {"totalGames":2, "games":gamesjson}    
    assert response.status_code == 200
    assert response.json() == testjson
    clear_tables()