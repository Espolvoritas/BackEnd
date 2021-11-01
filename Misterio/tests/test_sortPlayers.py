from pony.orm import db_session
from pony.orm import flush

import Misterio.database as db

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    db.db.create_tables()

def test_playing_order():
    '''Check if players are sorted at random correctly.'''

    clear_tables()
        
    print("\nTesting setNext, previousPlayer, and sortPlayers\n")
        
    with db_session:
        
        p1 = db.Player(nickName="Mr. Previous")
        p2 = db.Player(nickName="Mr. Next")
        p3 = db.Player(nickName="Mr. Evenafter")
        pls = [p1, p2, p3]
        flush()
            
        game = db.Game(name="Test order", host=p1, isStarted=False)
            
        for p in pls:
            game.addPlayer(p)
            
        for i, p in enumerate(pls):
            p.nextPlayer = pls[(i + 1) % 3]
                
        for p in pls:
            print(f"{p.nickName} == {p.nextPlayer.previousPlayer.nickName}")
            assert(p == p.nextPlayer.previousPlayer)
            
        print("\nNow we try shuffling our players... \n")
            
        game.sortPlayers()
        for p in pls:
            print(f"{p.nickName}'s next is now {p.nextPlayer.nickName}")
            
        print("Shuffle again a couple of times, to see if shuffling effectively shuffles:")
        
        distinctOrders = set()

        for i in [1, 2, 3, 4, 5, 6]:
            current = set()
            game.sortPlayers()
            for p in pls:
                print(f"{p.nickName}'s next is now {p.nextPlayer.nickName}")
                current.add(f"{p.nickName}'s next is now {p.nextPlayer.nickName}")
            print("")
            distinctOrders.add(frozenset(current))

        assert(len(distinctOrders)>0)

    clear_tables()
