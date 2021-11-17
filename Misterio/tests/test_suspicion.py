from fastapi.testclient import TestClient
from pony.orm import db_session, flush, select
from typing import Match
from fastapi import WebSocketDisconnect
from Misterio.functions import get_lobby_by_id
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

#TODO 
#test if suspicion is completely in envelope
#test if suspicion doesnt require picking

def test_automatic_response():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data1 = websocket1.receive_json()
            for player, expected in zip(data1["players"], expectedPlayers):
                assert (player["nickname"] == expected)
            print("Data1", data1)
            data2 = websocket2.receive_json()
            for player, expected in zip(data2["players"], expectedPlayers):
                assert (player["nickname"] == expected)
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
            for player, expected in zip(data["players"], expectedPlayers):
                assert (player["nickname"] == expected)
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    
    with db_session:
        player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
        player2 = player1.next_player        
        roomCards = select(c for c in player2.cards if c.card_type == "ROOM")
        roomCard = roomCards.first()
        room1 = db.Cell.get(room_name=roomCard.card_name)
        player1.location = room1
        cards1 = list(player1.cards)
        cards2 = list(player2.cards)
        monster = select(c for c in db.Card if c in player1.cards and c.is_monster()).first()
        victim = select(c for c in db.Card if c in player1.cards and c.is_victim()).first()
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
                print("Suspicion: ", victim, monster, roomCard.card_id )

                response = suspicion_post(player1.player_id, victim, monster, client)
                data2 = websocket2.receive_json()
                print("Sus broadcast 2: ", data2)
                
                #Turn change
                data1 = websocket1.receive_json()
                data2 = websocket2.receive_json()
                print("Turn change 1: ", data1)
                print("Turn change 2: ", data2)

                data2 = websocket2.receive_json()
                print("Player 2 sent card: ", data2)

                assert (response.status_code == 200)
                print(response)    
                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()
    

def test_makeSuspicion_2players():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data1 = websocket1.receive_json()
            for player, expected in zip(data1["players"], expectedPlayers):
                assert (player["nickname"] == expected)
            print("Data1", data1)
            data2 = websocket2.receive_json()
            for player, expected in zip(data2["players"], expectedPlayers):
                assert (player["nickname"] == expected)
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
            for player, expected in zip(data["players"], expectedPlayers):
                assert (player["nickname"] == expected)
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    
    with db_session:
        player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
        player2 = player1.next_player        
        roomCards = select(c for c in player2.cards if c.card_type == "ROOM")
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
                print("Suspicion: ", victim, monster, roomCard.card_id )

                websocket2.send_json({"code": "PICK_CARD", "card": victim})
                response = suspicion_post(player1.player_id, victim, monster, client)
                data2 = websocket2.receive_json()
                print("Sus broadcast 2: ", data2)
                
                #Turn change
                data1 = websocket1.receive_json()
                data2 = websocket2.receive_json()
                print("Turn change 1: ", data1)
                print("Turn change 2: ", data2)

                data2 = websocket2.receive_json()
                print("Player 2 pick card: ", data2)

                assert (response.status_code == 200)
                print(response)    
                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()


def test_makeSuspicion_3players():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    
    with db_session:
        lobby = get_lobby_by_id(lobby_id)
        lobby.is_started = True
        lobby.game = db.Game(lobby=lobby)
        player2 = db.Player(nickname=get_random_string(6), alive=True)
        player3 = db.Player(nickname=get_random_string(6), alive=True)
        lobby.add_player(player2)
        lobby.add_player(player3)
        lobby.game.sort_players()
        lobby.game.set_starting_positions()
        player1 = lobby.game.current_player
        player2 = player1.next_player
        player3 = player2.next_player
        lobby.game.fill_envelope()
        

        envelope = [lobby.game.monster, lobby.game.victim, lobby.game.room]
        available_cards = list(select(c for c in db.Card if c not in envelope).order_by(db.Card.card_id))
    
        player = lobby.game.current_player
        for c in available_cards:
            c.assign(player)
            player = player.next_player
        
        print(player1.cards)
        print(player2.cards)
        print(player3.cards)        

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

                    websocket3.send_json({"code": "PICK_CARD", "card": victim})
                    response = suspicion_post(player1.player_id, victim, monster, client)
                    data2 = websocket2.receive_json()
                    print("Sus broadcast 2: ", data2)
                    data3 = websocket3.receive_json()
                    print("Sus broadcast 3: ",data3)
                    
                    #Turn change
                    data1 = websocket1.receive_json()
                    data2 = websocket2.receive_json()
                    data3 = websocket3.receive_json()
                    print("Turn change 1: ", data1)
                    print("Turn change 2: ", data2)
                    print("Turn change 3: ", data3)

                    data3 = websocket3.receive_json()

                    print("False response 3: ", data3)

                    data3 = websocket3.receive_json()
                    print("Player3 pick card: ", data3)

                    data2 = websocket2.receive_json()
                    print("True response 2: ", data2)

                    assert (response.status_code == 200)
                    print(response)    

                    websocket3.close()
                    data1 = websocket1.receive_json()
                    data2 = websocket2.receive_json()
                    print("Disconnect player 3 (1): ", data1)
                    print("Disconnect player 3 (2): ", data2)
                    websocket2.close()
                    data1 = websocket1.receive_json()
                    print("Disconnect player 2: ", data1)
                    websocket1.close()
                except KeyboardInterrupt:
                    websocket2.close()
                    websocket1.close()

def test_invalid_suspicion():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data1 = websocket1.receive_json()

            data2 = websocket2.receive_json()
            response = start_game_post(1, client)
            assert (response.status_code == 200)

            data3 = websocket1.receive_json()

            data1 = websocket1.receive_json()
            data2 = websocket2.receive_json()

            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert (player["nickname"] == expected)
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    
    with db_session:
        player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
        player2 = player1.next_player
        room_cell = select(c for c in db.Cell if c.is_room()).first()
        player1.location = room_cell
        extra_player = db.Player(nickname="Invalid", alive=True)

    with client.websocket_connect("/gameBoard/" + str(player1.player_id)) as websocket1:
        currplayer = websocket1.receive_json()
        print(currplayer)
        with client.websocket_connect("/gameBoard/" + str(player2.player_id)) as websocket2:
            currplayer = websocket2.receive_json()#connection broadcast
            print(currplayer)
            try:
                #Suspicion outside turn
                print("Suspicion: ", 10, 1, 20)
                websocket2.send_json({"code": "PICK_CARD", "card": 10})
                response = suspicion_post(player2.player_id, 10, 1, client)
                assert (response.status_code == 403)
                
                #Suspicion invalid player
                print("Suspicion: ", 1, 10, 20)
                websocket2.send_json({"code": "PICK_CARD", "card": 10})
                response = suspicion_post(4, 14, 15, client)
                assert (response.status_code == 400)

                #Suspicion invalid game
                print("Suspicion: ", 1, 10, 20)
                websocket2.send_json({"code": "PICK_CARD", "card": 10})
                response = suspicion_post(extra_player.player_id, 14, 15, client)
                assert (response.status_code == 403)

                #Suspicion invalid cards
                print("Suspicion: ", 1, 10, 20)
                websocket2.send_json({"code": "PICK_CARD", "card": 10})
                response = suspicion_post(player1.player_id, 14, 15, client)
                assert (response.status_code == 403)

                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()

def test_invalid_room():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expectedPlayers = create_players(1, lobby_id)
    expectedPlayers.insert(0,host)
    
    with client.websocket_connect("/lobby/1") as websocket1, \
        client.websocket_connect("/lobby/2") as websocket2:
        try:
            data1 = websocket1.receive_json()

            data2 = websocket2.receive_json()
            response = start_game_post(1, client)
            assert (response.status_code == 200)

            data3 = websocket1.receive_json()

            data1 = websocket1.receive_json()
            data2 = websocket2.receive_json()

            websocket2.close()
            data = websocket1.receive_json()
            for player, expected in zip(data["players"], expectedPlayers):
                assert (player["nickname"] == expected)
            websocket1.close()
        except KeyboardInterrupt:
            websocket2.close()
            websocket1.close()
    
    with db_session:
        player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
        player2 = player1.next_player
        wrong_cell = select(c for c in db.Cell if not c.is_room()).first()
        player1.location = wrong_cell


    with client.websocket_connect("/gameBoard/" + str(player1.player_id)) as websocket1:
        currplayer = websocket1.receive_json()
        print(currplayer)
        with client.websocket_connect("/gameBoard/" + str(player2.player_id)) as websocket2:
            currplayer = websocket2.receive_json()#connection broadcast
            print(currplayer)
            try:
                #Suspicion outside room
                print("Suspicion: ", 10, 1, 20)
                websocket2.send_json({"code": "PICK_CARD", "card": 10})
                response = suspicion_post(player1.player_id, 10, 1, client)
                assert (response.status_code == 403)
            
                websocket2.close()
                data1 = websocket1.receive_json()
                print("Disconnect player 2: ", data1)
                websocket1.close()
            except KeyboardInterrupt:
                websocket2.close()
                websocket1.close()
                