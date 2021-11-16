from fastapi.testclient import TestClient
from pony.orm import db_session, select
from Misterio.functions import get_lobby_by_id
from Misterio.testing_utils import *
from Misterio.server import app
import Misterio.database as db

client = TestClient(app)

def test_automatic_response():
    db.clear_tables()
    host = get_random_string(6)
    lobby_id = create_game_post(host, client).json()["lobby_id"]
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)

    connect_and_start_game_2_players(expected_players, client)
    
    with db_session:
        player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
        player2 = player1.next_player 
        nickname1 = player1.nickname
        nickname2 = player2.nickname
        room_cards = select(c for c in player2.cards if c.is_room())
        room = room_cards.first()
        room_cell = db.Cell.get(room_name=room.card_name)
        player1.location = room_cell
        cards1 = list(player1.cards)
        cards2 = list(player2.cards)
        monster = select(c for c in db.Card if c in player1.cards and c.is_monster()).first()
        victim = select(c for c in db.Card if c in player1.cards and c.is_victim()).first()
        print(monster.card_name)
        print(victim.card_name)
        monster = monster.card_id
        victim = victim.card_id
        room = room.card_id

    with client.websocket_connect("/gameBoard/" + str(player1.player_id)) as websocket1:
        currplayer = websocket1.receive_json()
        print(currplayer)
        with client.websocket_connect("/gameBoard/" + str(player2.player_id)) as websocket2:
            currplayer = websocket2.receive_json()#connection broadcast
            print(currplayer)
            try:
                print("Player 1 Cards: ", cards1)
                print("Player 2 Cards: ", cards2)

                print("Suspicion: ", victim, monster, room)

                response = suspicion_post(player1.player_id, victim, monster, client)
                data2 = websocket2.receive_json()
                print("Sus broadcast 2: ", data2)
                assert (data2["code"] & 1)
                assert (data2["code"] & 4)
                assert (data2["victim"] == victim)
                assert (data2["monster"] == monster)
                assert (data2["room"] == room)
                assert (data2["current_player"] == nickname1)
                #Turn change
                data1 = websocket1.receive_json()
                assert (data1["code"] & 1)
                assert (data1["current_player"] == nickname2)
                data2 = websocket2.receive_json()
                assert (data2["code"] & 1)
                assert (data2["current_player"] == nickname2)
                print("Turn change 1: ", data1)
                print("Turn change 2: ", data2)

                data2 = websocket2.receive_json()
                assert (data2["code"] & 32)
                assert (data2["suspicion_player"] == nickname1)
                assert (data2["card"] == room)
                print("Player 2 sent card: ", data2)

                assert (response.status_code == 200)
                assert (response.json()["suspicion_card"] == room)
                print(response.json())    
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
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)
    
    with db_session:
        player1 = db.Lobby.get(lobby_id=lobby_id).game.current_player
        player2 = player1.next_player        
        room_cards = select(c for c in player2.cards if c.is_room())
        room = room_cards.first()
        room_cell = db.Cell.get(room_name=room.card_name)
        player1.location = room_cell
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
                print("Suspicion: ", victim, monster, room.card_id )

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

        room_cards = select(c for c in player3.cards if c.is_room())
        room = room_cards.first()
        room_cell = db.Cell.get(room_name=room.card_name)
        player1.location = room_cell
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
                    print("Suspicion: ", victim, monster, room.card_id )

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
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)

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
    expected_players = create_players(1, lobby_id)
    expected_players.insert(0,host)
    
    connect_and_start_game_2_players(expected_players, client)
    
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
                
