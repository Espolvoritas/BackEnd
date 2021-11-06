from fastapi.testclient import TestClient
from pony.orm import db_session
import string
import random # define the random module  

from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

def clear_tables():
    db.db.Player.cards.drop_table(with_all_data=True)
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Card, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Color, if_exists=True, with_all_data=True)
    db.db.create_tables()
    db.fillColors()
    db.fillCards()

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

@db_session
def add_player(nickName: str, game_id: int):
	game = db.Game.get(game_id=game_id)
	player = db.Player(nickName=nickName)
	game.addPlayer(player)

def create_players(quantity: int, game_id: int):
	player_list = []
	for x in range(quantity):
		new_player = get_random_string(6)
		add_player(new_player, game_id)
		player_list.append(new_player)
	return player_list

def create_new_game(nickName: str):
	return client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": nickName}
				)

def startGame(userID):
	return client.post("/lobby/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json=f'{userID}'
				)

#make sure that no player gets an envelope card
def test_envelope():
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame(1)
			assert response.status_code == 200
			with db_session:
				playerCards = []
				game = db.Game.get(game_id=game_id)
				for player in expectedPlayers:
					playerCards.append(list(db.Player.get(nickName=player).cards))
				assert game.culprit not in playerCards
				assert game.room not in playerCards
				assert game.victim not in playerCards
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

#make sure that no player gets a duplicated cars
def test_duplcation():
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame(1)
			assert response.status_code == 200
			with db_session:
				game = db.Game.get(game_id=game_id)
				cards1 = list(db.Player.get(nickName=host).cards)
				cards2 = list(db.Player.get(nickName=expectedPlayers[1]).cards)
				for card in cards1:
					assert card not in cards2
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()

def test_random_first():
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame(1)
			assert response.status_code == 200
			with db_session:
				first_player = db.Game.get(game_id=game_id).currentPlayer
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	clear_tables()
	host = get_random_string(6)
	game_id = create_new_game(host).json()['game_id']
	expectedPlayers = create_players(1,game_id)
	expectedPlayers.insert(0,host)
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected

			response = startGame(1)
			assert response.status_code == 200
			with db_session:
				second_player = db.Game.get(game_id=game_id).currentPlayer
			assert first_player != second_player
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert player['nickName'] == expected
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	