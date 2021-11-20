from pony.orm import db_session
from pony.orm import flush

import Misterio.database as db

def test_playing_order():
    """Check if players are sorted at random correctly."""

    db.clear_tables()
        
    print("\nTesting setNext, next_player_of, and sort_players\n")
        
    with db_session:
        
        p1 = db.Player(nickname="Mr. Previous")
        p2 = db.Player(nickname="Mr. Next")
        p3 = db.Player(nickname="Mr. Evenafter")
        pls = [p1, p2, p3]
        flush()
            
        lobby = db.Lobby(name="Test order", host=p1, is_started=False)
        lobby.game = db.Game(lobby=lobby)
        lobby.is_started = True
            
        for p in pls:
            lobby.add_player(p)
            
        for i, p in enumerate(pls):
            p.next_player = pls[(i + 1) % 3]
                
        for p in pls:
            print(f"{p.nickname} == {p.next_player.next_player_of.nickname}")
            assert(p == p.next_player.next_player_of)
            
        print("\nNow we try shuffling our players... \n")
            
        lobby.game.sort_players()
        for p in pls:
            print(f"{p.nickname}'s next is now {p.next_player.nickname}")
            
        print("Shuffle again a couple of times, to see if shuffling effectively shuffles:")
        
        distinctOrders = set()

        for i in [1, 2, 3, 4, 5, 6]:
            current = set()
            lobby.game.sort_players()
            for p in pls:
                print(f"{p.nickname}'s next is now {p.next_player.nickname}")
                current.add(f"{p.nickname}'s next is now {p.next_player.nickname}")
            print("")
            distinctOrders.add(frozenset(current))

        assert(len(distinctOrders)>0)

    db.clear_tables()
