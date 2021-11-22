from pony.orm import db_session, select, flush, commit
from Misterio.functions import get_card_by_id
from Misterio.tests import test_accuse, test_suspicion, test_move_player
import Misterio.database as db

def test_player_creation():
    name = "test_player"
    #print("Creating player test_player...")
    with db_session:
        test_player = db.Player(nickname=name)
        commit()
        query = select(p for p in db.Player if p.nickname == name)
        result = query.first()
    assert (result.nickname == test_player.nickname)
    db.clear_tables()
    
def test_player_deletion():
    name = "test_player"
    #print("Creating player test_player...")
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
        #print("Creating some players...")
        host = db.Player(nickname="eladmin")
        player1 = db.Player(nickname="Jorge")
        player2 = db.Player(nickname="Roberto")
        player3 = db.Player(nickname="Rosa Helena")
        players = [host, player1, player2, player3]
        flush()
        #print("Creating a game...")
        game = db.Lobby(name="Los mas latinos", host=host, is_started=False)
        flush()
        #print("Trying to add those mock players to the game...")
        game.add_player(host)
        game.add_player(player1)
        game.add_player(player2)
        game.add_player(player3)
        flush()
        commit()

        i = 0
        #print("\nShowing mock players...")
        players_query = select(p for p in game.players).order_by(lambda p: p.player_id)
        
        for player, expected in zip(players_query, players) :
            #print(f"Player nickname: {player.nickname}")
            #print(f"Expected nickname: {expected.nickname}")
            assert (player.lobby == game)
            expected = players[i]
            assert (player.nickname == expected.nickname )
            i += 1
        

        all_players = list(select(p for p in game.players))
        #print("\nNumber of players who joined the game:")
        #print(f"{len(all_players)}\n")

        assert len(all_players) == 4
        assert game.player_count == 4

    db.clear_tables()

def test_stats():
    with db_session:
        gamestats = db.Stats.get(stats_id=1)
        wrong_acc = gamestats.wrong_accusations
        right_acc = gamestats.right_accusations
        sus_made = gamestats.suspicions_made
        won = gamestats.won_games
        traps = gamestats.trap_falls

    test_suspicion.test_makeSuspicion_2players()
    test_accuse.test_right_accusation()
    test_accuse.test_wrong_accusation()
    test_move_player.test_trap()

    with db_session:
        gamestats = db.Stats.get(stats_id=1)
        assert (wrong_acc < gamestats.wrong_accusations)
        assert (right_acc < gamestats.right_accusations)
        assert (sus_made < gamestats.suspicions_made)
        assert (won < gamestats.won_games)
        assert (traps < gamestats.trap_falls)
        print("Most chosen color: ", gamestats.most_chosen_color())
        top_monster, top_victim, top_room = gamestats.envelope_top_cards()
        assert (get_card_by_id(top_monster).is_monster())
        assert (get_card_by_id(top_victim).is_victim())
        assert (get_card_by_id(top_room).is_room())
        print("Top monster: ", top_monster, "Top victim: ", top_victim, "Top room: ", top_room)
        print("Average game time: ", gamestats.get_average_game_time())

