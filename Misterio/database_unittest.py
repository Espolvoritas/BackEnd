import unittest
import database as db
from pony.orm import Database, db_session
from pony.orm import select, flush, commit

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    
    db.db.create_tables()


class TestPlayer(unittest.TestCase):

    def test_player_creation(self):
        name = "testPlayer"
        print("Creating player testPlayer...")
        with db_session:
            testPlayer = db.Player(nickname=name)
            commit()
            query = select(p for p in db.Player if p.nickname == name)
            result = query.first()
        self.assertEqual(result.nickname, testPlayer.nickname)
        clear_tables()
        
    def test_player_deletion(self):
        name = "testPlayer"
        print("Creating player testPlayer...")
        with db_session:
            testPlayer = db.Player(nickname=name)
            commit()
            db.Player[testPlayer.player_id].delete()
            flush()
            result = list(select(p for p in db.Player))
        self.assertListEqual(result, [])
        clear_tables()
    

class TestGame(unittest.TestCase):
    
    def test_game_creation(self):
        '''Check if a game entity instance can be created succesfully.'''
        game_name = "Espolvoritas 4ever"
        with db_session:
            host = db.Player(nickname="eladmin")
            commit()
            new_game = db.Game(name=game_name, isStarted=False, host=host)
            query = select(g for g in db.Game if g.name == game_name)
            result = query.first()
        self.assertEqual(new_game.name, result.name)
        clear_tables()
 
    def test_adding_players(self):
        '''Check if players can be added to a game safely 
        with the expected results.'''

        with db_session:

            print("Creating some players...")
            host = db.Player(nickname="eladmin")
            player1 = db.Player(nickname="Jorge")
            player2 = db.Player(nickname="Roberto")
            player3 = db.Player(nickname="Rosa Helena")
            players = [host, player1, player2, player3]
            flush()
            print("Creating a game...")
            game = db.Game(name="Los mas latinos", host=host, isStarted=False)
            flush()
            print("Trying to add those mock players to the game...")
            game.addPlayer(host)
            game.addPlayer(player1)
            game.addPlayer(player2)
            game.addPlayer(player3)
            flush()
            commit()

            i = 0
            print("\nShowing mock players...")
            idSort = lambda p: p.player_id
            players_query = select(p for p in game.players).order_by(idSort)
           
            for player, expected in zip(players_query, players):
                print(f"Player nickname: {player.nickname}")
                print(f"Expected nickname: {expected.nickname}")
                self.assertEqual(player.lobby, game)
                expected = players[i]
                self.assertEqual(player.nickname, expected.nickname)
                i += 1
            
            all_players = list(select(p for p in game.players))
            print("\nNumber of players who joined the game:")
            print(f"{game.playerCount}\n")

            self.assertEqual(len(all_players), 4)
            self.assertEqual(game.playerCount, 4)

        clear_tables()

    def test_playing_order(self):
        '''Check if players are sorted at random correctly.'''
        
        print("\nTesting setNext, previousPlayer, and sortPlayers\n")
        
        with db_session:
        
            p1 = db.Player(nickname="Mr. Previous")
            p2 = db.Player(nickname="Mr. Next")
            p3 = db.Player(nickname="Mr. Evenafter")
            pls = [p1, p2, p3]
            flush()
            
            game = db.Game(name="Test order", host=p1, isStarted=False)
            
            for p in pls:
                game.addPlayer(p)
            
            for i, p in enumerate(pls):
                p.nextPlayer = pls[(i + 1) % 3]
                
            for p in pls:
                print(f"{p.nickname} == {p.nextPlayer.previousPlayer.nickname}")
                self.assertEqual(p, p.nextPlayer.previousPlayer)
            
            print("\nNow we try shuffling our players... \n")
            
            game.sortPlayers()
            for p in pls:
                print(f"{p.nickname}'s next is now {p.nextPlayer.nickname}")
            
            print("Shuffle again a couple of times, to see if shuffling effectively shuffles:")
            
            for i in [1, 2, 3, 4]:
                game.sortPlayers()
                for p in pls:
                    print(f"{p.nickname}'s next is now {p.nextPlayer.nickname}")
                print("")

if __name__ == '__main__':
    unittest.main()
