from fastapi.testclient import TestClient
from pony.orm import db_session, flush, select
from typing import Match
import string
import pytest
import random # define the random module  
from fastapi import WebSocketDisconnect
from time import sleep
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

#TODO 
#test if suspicion is completely in envelope
#test if suspicion doesnt require picking

def test_makeSuspicion_2players():
	db.clear_tables()
	host = get_random_string(6)
	lobby_id = create_game_post(host, client).json()['lobby_id']
	expectedPlayers = create_players(1, lobby_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2:
		try:
			data1 = websocket1.receive_json()
			for player, expected in zip(data1['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			print("Data1", data1)
			data2 = websocket2.receive_json()
			for player, expected in zip(data2['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			print("data2", data2)
			response = start_game_post(1, client)
			assert (response.status_code == 200)

			data3 = websocket1.receive_json()
			print("data3", data3)

			data1 = websocket1.receive_json()
			data2 = websocket2.receive_json()
			print(data1)
			print(data2)
			
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			websocket1.close()
		except KeyboardInterrupt:
			websocket2.close()
			websocket1.close()
	
	with db_session:
		player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
		player2 = player1.next_player
		player1.inRoom = True
		
		roomCards = select(c for c in player2.cards if c.card_type == 'Room')
		roomCard = roomCards.first()
		room1 = db.Cell.get(room_name=roomCard.card_name)
		player1.location = room1
		cards1 = list(player1.cards)
		cards2 = list(player2.cards)
		monster = select(c for c in db.Card if c in player2.cards and c.is_monster()).first()
		victim = select(c for c in db.Card if c in player2.cards and c.is_victim()).first()
		print(monster.card_name)
		print(victim.card_name)
		monster = monster.card_id
		victim = victim.card_id
	with client.websocket_connect("/gameBoard/" + str(player1.player_id)) as websocket1:
		currplayer = websocket1.receive_json()
		print(currplayer)
		with client.websocket_connect("/gameBoard/" + str(player2.player_id)) as websocket2:
			currplayer = websocket2.receive_json()#connection broadcast
			print(currplayer)
			try:
				print("Player 1 Cards: ", cards1)
				print("Player 2 Cards: ", cards2)
				
				websocket2.send_json({'code': 'PICK_CARD', 'card': victim})
				response = suspicion_post(player1.player_id, victim, monster, client)
				
				data2 = websocket2.receive_json()
				
				print(data2)

				data2 = websocket2.receive_json()
				print(data2)
				
				data1 = websocket1.receive_json()
				data2 = websocket2.receive_json()
				print(data1)
				print(data2)

				data1 = websocket1.receive_json()
				data2 = websocket2.receive_json()
				print(data1)
				print(data2)

				assert (response.status_code == 200)
				print(response)	

				websocket2.close()
				data1 = websocket1.receive_json()
				print(data1)
				websocket1.close()
			except KeyboardInterrupt:
				websocket2.close()
				websocket1.close()


def test_makeSuspicion_3players():
	db.clear_tables()
	host = get_random_string(6)
	lobby_id = create_game_post(host, client).json()['lobby_id']
	expectedPlayers = create_players(2, lobby_id)
	expectedPlayers.insert(0,host)
	
	with client.websocket_connect("/lobby/1") as websocket1, \
		client.websocket_connect("/lobby/2") as websocket2, \
		client.websocket_connect("/lobby/3") as websocket3:
		try:
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			data = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			data = websocket3.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickname'] == expected)

			response = start_game_post(1, client)
			assert (response.status_code == 200)
			websocket3.close()
			data = websocket1.receive_json()
			data2 = websocket2.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			for player, expected in zip(data2['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			websocket2.close()
			data = websocket1.receive_json()
			for player, expected in zip(data['players'], expectedPlayers):
				assert (player['nickname'] == expected)
			websocket1.close()
		except KeyboardInterrupt:
			websocket3.close()
			websocket2.close()
			websocket1.close()
	
	with db_session:
		player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
		player2 = player1.next_player
		player3 = player2.next_player
		
		roomCards = select(c for c in player3.cards if c.is_room())
		roomCard = roomCards.first()
		room1 = db.Cell.get(room_name=roomCard.card_name)
		player1.location = room1
		cards1 = list(player1.cards)
		cards2 = list(player2.cards)
		cards3 = list(player3.cards)
		monster = select(c for c in db.Card if c in player3.cards and c.is_monster()).first()
		victim = select(c for c in db.Card if c in player3.cards and c.is_victim()).first()
		monster = monster.card_id
		victim = victim.card_id
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
					print("Suspicion: ", victim, monster, roomCard.card_id )

					websocket3.send_json({'code': 'PICK_CARD', 'card': victim})
					response = suspicion_post(player1.player_id, victim, monster, client)
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