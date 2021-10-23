from server import app
from fastapi.testclient import TestClient
import string
from time import sleep
import database as db
from pony.orm import db_session, flush, select
import random # define the random module  

client = TestClient(app)

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    
    db.db.create_tables()

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def add_player(nickName: str, game_id: int):
	with db_session:
		game = db.Game.get(game_id=game_id)
		player = db.Player(nickName=nickName)
		flush()
		game.addPlayer(player)

def create_players(quantity: int, game_id: int):
	player_list = []
	for x in range(quantity):
		new_player = get_random_string(6)
		add_player(new_player, game_id)
		player_list.append(new_player)
	return player_list

def create_new_game(nickName: str):
	return client.post("/game/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": nickName}
				)

def create_player():
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']

def test_get_two_players():
	
	#expectedPlayers = create_players(1,game_id)
	#expectedPlayers.insert(0,host)
	with client.websocket_connect("/gameBoard/1/rollDice") as websocket1:
		try:
			websocket1.send_text(1)
			sleep(5)
			websocket1.close()
			print("closed")
		except KeyboardInterrupt:
			websocket1.close()
	

#create_player()
test_get_two_players()