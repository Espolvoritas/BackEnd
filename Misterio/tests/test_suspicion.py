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

def test_makeSuspicion():
	db.clear_tables()
	host = get_random_string(6)
	game_id = create_game_post(host, client).json()['game_id']
	expectedPlayers = create_players(1, game_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)

			response = startGame_post(1, client)
			assert (response.status_code == 200)
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickName'] == expected)
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	
	with db_session:
		player1 = db.Game.get(game_id=game_id).currentPlayer
		player2 = player1.nextPlayer
		player1.inRoom = True
		
		roomCards = select(c for c in player2.cards)
		roomCard = roomCards.first()
		room1 = db.Cell()
		room1.roomName = roomCard.cardName
		player1.location = room1
		suspicion = []
		suspicion.append(list(player2.cards).pop().cardId)
		suspicion.append(list(player1.cards).pop().cardId)
	with client.websocket_connect("/gameBoard/" + str(player1.player_id)) as websocket1:
		currplayer = websocket1.receive_json()
		with client.websocket_connect("/gameBoard/" + str(player2.player_id)) as websocket2:
			try:
				currplayer = websocket2.receive_json()#connection broadcast
				websocket1.send_json({'status': 'SUSPICION', 'args': suspicion})		
				websocket2.send_json({'status': 'INVALIDCOMMAND', 'args': suspicion})#just to keep websocket2 waiting
										
				data2 = websocket2.receive_json()
				assert (len(data2['args']) != 0)
				print(data2)
				websocket2.send_json({'status': 'PICK_CARD', 'args': [roomCard.cardId]})
				data1 = websocket1.receive_json()
				data2 = websocket2.receive_json()
				assert (data1['args'][0])
				assert (data2['args'][0])
				
				print(data1)
				print(data2)
				data1 = websocket1.receive_json()
				print(data1)
				if (data1['status'] == 'SUSPICION_RESPONDED'):
					assert (roomCard.cardId == data1['args'].pop())
				data1 = websocket1.receive_json()
				data2 = websocket2.receive_json()
				print(data1)
				print(data2)
				websocket2.close()
				data1 = websocket1.receive_json()
				print(data1)
				websocket1.close()
			except KeyboardInterrupt:
				websocket1.close()