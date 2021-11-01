from pony.orm import db_session, select, flush, commit
import unittest

import Misterio.database as db

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    
    db.db.create_tables()


class TestPlayer(unittest.TestCase):

    def test_player_creation(self):
        name = "testPlayer"
        print("Creating player testPlayer...")
        with db_session:
            testPlayer = db.Player(nickName=name)
            commit()
            query = select(p for p in db.Player if p.nickName == name)
            result = query.first()
        self.assertEqual(result.nickName, testPlayer.nickName)
        clear_tables()
        
    def test_player_deletion(self):
        name = "testPlayer"
        print("Creating player testPlayer...")
        with db_session:
            testPlayer = db.Player(nickName=name)
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
            host = db.Player(nickName="eladmin")
            commit()
            new_game = db.Game(name=game_name, isStarted=False, host=host)
            query = select(g for g in db.Game if g.name == game_name)
            result = query.first()
        self.assertEqual(new_game.name, result.name )
        clear_tables()

    
    def test_adding_players(self):
        '''Check if players can be added to a game safely 
        with the expected results.'''

        with db_session:

            print("Creating some players...")
            host = db.Player(nickName="eladmin")
            player1 = db.Player(nickName="Jorge")
            player2 = db.Player(nickName="Roberto")
            player3 = db.Player(nickName="Rosa Helena")
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
            players_query = select(p for p in game.players).order_by(lambda p: p.player_id)
           
            for player, expected in zip(players_query, players) :
                print(f"Player nickname: {player.nickName}")
                print(f"Expected nickname: {expected.nickName}")
                self.assertEqual(player.lobby, game)
                expected = players[i]
                self.assertEqual(player.nickName, expected.nickName )
                i += 1
            

            all_players = list(select(p for p in game.players))
            print("\nNumber of players who joined the game:")
            print(f"{len(all_players)}\n")

            self.assertEqual(len(all_players), 4)
            self.assertEqual(game.playerCount, 4)

        clear_tables()

if __name__ == '__main__':
    unittest.main()