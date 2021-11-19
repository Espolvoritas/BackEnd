from pony.orm import db_session, select, flush, commit

import Misterio.database as db

def test_player_creation():
    name = "test_player"
    print("Creating player test_player...")
    with db_session:
        test_player = db.Player(nickname=name)
        commit()
        query = select(p for p in db.Player if p.nickname == name)
        result = query.first()
    assert (result.nickname == test_player.nickname)
    db.clear_tables()
    
def test_player_deletion():
    name = "test_player"
    print("Creating player test_player...")
    with db_session:
        test_player = db.Player(nickname=name)
        commit()
        db.Player[test_player.player_id].delete()
        flush()
        result = list(select(p for p in db.Player))
    assert not result 
    db.clear_tables()
    

def test_game_creation():
    """Check if a game entity instance can be created succesfully."""
    game_name = "Espolvoritas 4ever"
    with db_session:
        host = db.Player(nickname="eladmin")
        commit()
        new_game = db.Lobby(name=game_name, is_started=False, host=host)
        query = select(g for g in db.Lobby if g.name == game_name)
        result = query.first()
    assert new_game.name == result.name 
    db.clear_tables()

    
def test_adding_players():
    """Check if players can be added to a game safely 
    with the expected results."""

    with db_session:
        print("Creating some players...")
        host = db.Player(nickname="eladmin")
        player1 = db.Player(nickname="Jorge")
        player2 = db.Player(nickname="Roberto")
        player3 = db.Player(nickname="Rosa Helena")
        players = [host, player1, player2, player3]
        flush()
        print("Creating a game...")
        game = db.Lobby(name="Los mas latinos", host=host, is_started=False)
        flush()
        print("Trying to add those mock players to the game...")
        game.add_player(host)
        game.add_player(player1)
        game.add_player(player2)
        game.add_player(player3)
        flush()
        commit()

        i = 0
        print("\nShowing mock players...")
        players_query = select(p for p in game.players).order_by(lambda p: p.player_id)
        
        for player, expected in zip(players_query, players) :
            print(f"Player nickname: {player.nickname}")
            print(f"Expected nickname: {expected.nickname}")
            assert (player.lobby == game)
            expected = players[i]
            assert (player.nickname == expected.nickname )
            i += 1
        

        all_players = list(select(p for p in game.players))
        print("\nNumber of players who joined the game:")
        print(f"{len(all_players)}\n")

        assert len(all_players) == 4
        assert game.player_count == 4

    db.clear_tables()
