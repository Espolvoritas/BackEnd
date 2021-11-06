from fastapi.testclient import TestClient
from pony.orm import db_session, flush, select
from typing import Match
import string
import pytest
import random # define the random module  
from fastapi import WebSocketDisconnect
from time import sleep
from Misterio.functions import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

#TODO 
#test if suspicion is completely in envelope
#test if suspicion doesnt require picking

def test_makeSuspicion_3players():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(2, game_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2, \
		client.websocket_connect("/lobby/3") as websocket3:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			data = websocket3.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)

			response = startGame_post(1, client)
			assert (response.status_code == 200)
			websocket3.close()
			data = websocket1.receive_json()
			data2 = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			for player, expected in zip(data2['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			websocket1.close()
		except KeyboardInterrupt:
			websocket3.close()
			websocket2.close()
			websocket1.close()
	
	with db_session:
		player1 = db.Game.get(game_id=game_id).currentPlayer
		player2 = player1.nextPlayer
		player3 = player2.nextPlayer
		player1.inRoom = True
		
		roomCards = select(c for c in player3.cards if c.cardType == 'Room')
		roomCard = roomCards.first()
		room1 = db.Cell()
		room1.roomName = roomCard.cardName
		player1.location = room1
		cards1 = list(player1.cards)
		cards2 = list(player2.cards)
		cards3 = list(player3.cards)
		roomcard = db.Card.get(cardName=room1.roomName)
		culprit = select(c for c in db.Card if c in player3.cards and c.cardType == 'Monster').first()
		victim = select(c for c in db.Card if c in player3.cards and c.cardType == 'Victim').first()
		print(culprit.cardName)
		print(victim.cardName)
		culprit = culprit.cardId
		victim = victim.cardId
	with client.websocket_connect("/gameBoard/" + str(player1.player_id)) as websocket1:
		currplayer = websocket1.receive_json()
		with client.websocket_connect("/gameBoard/" + str(player2.player_id)) as websocket2:
			currplayer = websocket2.receive_json()#connection broadcast
			with client.websocket_connect("/gameBoard/" + str(player3.player_id)) as websocket3:
				try:
					currplayer = websocket3.receive_json()#connection broadcast

					print("Player 1 Cards: ", cards1)
					print("Player 2 Cards: ", cards2)
					print("Player 3 Cards: ", cards3)
					print("Suspicion: ", victim, culprit, roomCard.cardId )

					websocket3.send_json({'status': 'PICK_CARD', 'args': [victim]})
					response = suspicion_post(player1.player_id, victim, culprit, client)
					data1 = websocket1.receive_json()
					data2 = websocket2.receive_json()
					data3 = websocket3.receive_json()
					print(data1)
					print(data2)
					print(data3)
					data3 = websocket3.receive_json()
					print(data3)
					data1 = websocket1.receive_json()
					data2 = websocket2.receive_json()
					data3 = websocket3.receive_json()
					print(data1)
					print(data2)
					print(data3)
					assert (response.status_code == 200)
					print(response)	
					websocket3.close()
					data1 = websocket1.receive_json()
					data2 = websocket2.receive_json()
					print(data1)
					print(data2)
					websocket2.close()
					data1 = websocket1.receive_json()
					print(data1)
					websocket1.close()
				except KeyboardInterrupt:
					websocket2.close()
					websocket1.close()