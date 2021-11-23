from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, HTTPException, Body, websockets
from pony.orm import db_session, select
from asyncio import sleep
from random import choice
import logging

from Misterio.constants import *
from Misterio.functions import *
import Misterio.database as db
import Misterio.manager as mng

from starlette.responses import Response


gameBoard = APIRouter(prefix="/gameBoard")
logger = logging.getLogger("gameboard")

game_manager = mng.GameBoardManager()


@gameBoard.post("/turnYield", status_code=status.HTTP_200_OK)
async def yield_turn(player_id: int = Body(...)):
    if player_in_turn(player_id):
        player = get_player_by_id(player_id)
        with db_session:
            lobby_id = player.lobby.lobby_id
        await game_manager.update_turn(lobby_id)
        broadcast = {
            "code": WS_CHAT_MSG,
            "msg":{"user": "Sistema", "color": 0,"str": "El jugador " +
            str(get_player_nickname(player_id)) + " se quedo sin tiempo y perdio el turno"}
        }
        await game_manager.lobby_broadcast(broadcast, lobby_id)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

#todo check cost < roll and check new_position is in movement range
@gameBoard.post("/moves", status_code=status.HTTP_200_OK)
async def get_moves(player_id: int = Body(...), x: int = Body(...), y: int = Body(...), remaining: int = Body(...)):
    room = 0
    moves = []
    trapped = False
    with db_session:
        player = get_player_by_id(player_id)
        clear_player_status(player)
        new_position = get_cell_by_coordinates(x, y)
        if not new_position or player != player.lobby.game.current_player:
            raise HTTPException(status.HTTP_400_BAD_REQUEST)
        player.location = new_position
        if new_position.is_room():
            room = get_room_cell_id(new_position.room_name)
            player.set_roll(0)
        else:
            player.set_roll(remaining)
            moves=get_reachable(player_id)
        if room == 0 and remaining == 0 and "ENTRANCE-" not in new_position.cell_type:
            trapped = new_position.cell_type == "TRAP"
            await game_manager.update_turn(player.lobby.lobby_id)
    position_broadcast = {
        "code": WS_POS_LIST,
        "positions": get_position_list(player.lobby.lobby_id)
    }
    if trapped:
        position_broadcast.update({
            "msg":{"user": "Sistema", "color": 0,"str": "El jugador " +
            str(get_player_nickname(player_id)) + " cayo en una trampa"}
        })
        position_broadcast["code"] += WS_CHAT_MSG
    await game_manager.lobby_broadcast(position_broadcast, player.lobby.lobby_id)
    return {"moves" : moves, "room": room, "trapped": trapped}

@gameBoard.post("/accuse")
async def accuse(room: int = Body(...), monster: int = Body(...), victim: int = Body(...), player_id: int = Body(...)):
    with db_session:
        player = get_player_by_id(player_id)
        global_stats = db.Stats.get(stats_id = 1)
        if not player or not player.lobby or not player.alive:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="... why?")
        lobby = player.lobby
        won = lobby.game.win_check(monster, victim, room)
        status_broadcast = {
            "code": WS_ACCUSATION,
            "data": {
                "player": player.nickname,
                "won": won
            }
        }
        envelope = [lobby.game.monster.card_id, lobby.game.victim.card_id, lobby.game.room.card_id]
        if won:
            status_broadcast["data"]["envelope"] = envelope
            global_stats.right_accusations += 1
            global_stats.won_games += 1
            elapsed = lobby.game.get_game_duration()
            global_stats.game_data["time"].append(elapsed)
        await game_manager.lobby_broadcast(status_broadcast, lobby.lobby_id)
        await game_manager.update_turn(lobby.lobby_id)
        if not won:
            player.commit_die()
            global_stats.wrong_accusations += 1
        if all_dead(lobby.lobby_id):
            global_stats.lost_games += 1
            elapsed = lobby.game.get_game_duration()
            global_stats.game_data["time"].append(elapsed)
            await game_manager.lobby_broadcast({"code": WS_LOST, "envelope": envelope}, lobby.lobby_id)

@gameBoard.post("/rollDice", status_code=status.HTTP_200_OK)
async def roll_dice(player_id: int = Body(...), roll: int = Body(...)):
    if player_in_turn(player_id):
        with db_session:
            player = get_player_by_id(player_id)
            player.set_roll(roll)
        return {"moves" : get_reachable(player_id)}
    else:
        raise HTTPException(status_code=403, detail="Player can't roll dice outside his/her turn.")

@gameBoard.post("/checkSuspicion", status_code=status.HTTP_200_OK)
async def check_suspicion(player_id: int = Body(...), victim_id: int = Body(...), monster_id: int = Body(...)):
    with db_session:
        player = get_player_by_id(player_id)
        victim = get_card_by_id(victim_id)
        monster = get_card_by_id(monster_id)
        if player is None:
            raise HTTPException(status_code=400, detail="Player does not exist")
        lobby = player.lobby
        if lobby is None:
            raise HTTPException(status_code=403, detail="Player is not in game.")
        if not player_in_turn(player_id):
            raise HTTPException(status_code=403, detail="Player can't make a suspicion outside his/her turn.")
        if not player.location.is_room():
            raise HTTPException(status_code=403, detail="Player must be in a room to make a suspicion.")
        if (not victim.is_victim() or not monster.is_monster()):
            raise HTTPException(status_code=403, detail="Suspicion card types are invalid.")
        else:
            room_id = get_room_card_id(player.location.room_name)
            players = []
            currplayer_id = player.next_player.player_id
            player.set_roll(0)
            for i in range(lobby.player_count-1):
                currplayer = get_player_by_id(currplayer_id)
                currplayer_cards = get_card_list(currplayer_id)
                players.append([currplayer.player_id, currplayer.nickname, currplayer_cards])
                currplayer_id = currplayer.next_player.player_id
            players.reverse()
            suspicion = [monster_id, victim_id, room_id]
            global_stats = db.Stats.get(stats_id = 1)
            global_stats.suspicions_made += 1

    suspicion_broadcast = {
        "code": WS_CURR_PLAYER + WS_SUSPICION,
        "current_player": player.nickname,
        "victim": victim_id,
        "monster": monster_id,
        "room": room_id
    }
    sus_websocket = game_manager.get_websocket(player_id,lobby.lobby_id)
    await game_manager.almost_lobby_broadcast(suspicion_broadcast, [sus_websocket],lobby.lobby_id)
    await game_manager.update_turn(lobby.lobby_id)
    suspicion_card, response_player = await check_player_cards(players, player.nickname, sus_websocket, suspicion, lobby.lobby_id)
    return {"response_player": response_player, "suspicion_card": suspicion_card}
    
async def check_player_cards(players: list, suspicion_player: str, sus_websocket: WebSocket, suspicion: list, lobby_id: int):
    responded = False
    timer = 0
    response_player = ""
    game_manager.set_pick_card(lobby_id,None)
    suspicion_card = None
    while (not responded and len(players)>0):
        next_player = players.pop()
        matches = []
        for card in suspicion:
            if card in next_player[2]:
                matches.append(card)
        response_player = next_player[1]
        res_websocket = game_manager.get_websocket(next_player[0], lobby_id)
        if matches:
            if len(matches) > 1:
                #player went afk before suspicion
                if is_afk(next_player[0]):
                    suspicion_card = choice(matches)
                else:
                    response_message = {"code": WS_PICK_CARD, "matching_cards": matches}
                    #Send next player the option to pick a card
                    await game_manager.send_personal_message(response_message, res_websocket)
                    while suspicion_card is None and timer < CHOOSE_CARD_TIMER:
                        suspicion_card = game_manager.get_pick_card(lobby_id)
                        #Await for next player to pick a card to show (maybe implement timer)
                        await sleep(1)
                        timer+=1
                    if  suspicion_card is None:
                        suspicion_card = choice(matches)
            else:
                suspicion_card = matches.pop()
                response_message = {
                    "code": WS_SENT_CARD_NOTIFY,
                    "suspicion_player": suspicion_player,
                    "card": suspicion_card
                }
                await game_manager.send_personal_message(response_message, res_websocket)
            responded = True
        response_broadcast = {
            "code": WS_SUSPICION_STATUS,
            "responded": responded,
            "suspicion_player": suspicion_player,
            "response_player": response_player
        }
        #Broadcast suspicion status to all players except who responded and who made the suspicion
        await game_manager.almost_lobby_broadcast(response_broadcast, [res_websocket, sus_websocket], lobby_id)
    
    return suspicion_card, response_player

@gameBoard.post("/salemsWitch")
async def use_salems_witch(player_id: int = Body(...)):
    envelope_card = None
    with db_session:
        player = get_player_by_id(player_id)
        if player is None:
            raise HTTPException(status_code=400, detail="Player does not exist")
        lobby = player.lobby
        if lobby is None:
            raise HTTPException(status_code=403, detail="Player is not in game.")
        if not player_in_turn(player_id):
            raise HTTPException(status_code=403, detail="Player can't use Salem's witch outside his/her turn.")
        salem_card = get_card_by_id(21)
        player_cards = get_card_list(player_id)
        if not salem_card.card_id in player_cards:
            raise HTTPException(status_code=403, detail="Player doesn't have Salem's witch card or has already used it.")
        else:
            envelope = [lobby.game.monster.card_id, lobby.game.victim.card_id, lobby.game.room.card_id]
            envelope_card = choice(envelope)
            player.cards.remove(salem_card)
    message = {
        "code": WS_SALEM,
        "current_player": get_current_turn(lobby.lobby_id),
    }
    websocket = game_manager.get_websocket(player_id, lobby.lobby_id)
    await game_manager.almost_lobby_broadcast(message, [websocket], lobby.lobby_id)
    return {"envelope_card": envelope_card}


@gameBoard.websocket("/gameBoard/{player_id}")
async def handle_turn(websocket: WebSocket, player_id: int):
    
    with db_session:
        player = get_player_by_id(player_id)
        if player is None or player.lobby is None or game_manager.exists(player_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        lobby = player.lobby
        player_name = get_player_nickname(player_id)
        player_color = get_player_color(player_id)
        await game_manager.connect(websocket, player_id)
        message = {
            "code": WS_CURR_PLAYER + WS_CARD_LIST +    WS_POS_LIST,
            "current_player": get_current_turn(lobby.lobby_id),
            "cards": get_card_list(player_id),
            "positions": get_position_list(lobby.lobby_id)
        }
        await game_manager.send_personal_message(message,websocket)

    try:
        while(True):
            message = await websocket.receive_json()
            if message["code"] == "PICK_CARD":
                game_manager.set_pick_card(lobby.lobby_id,message["card"])
            elif message['code'] & WS_CHAT_MSG:
                broadcast = {
                    "code": WS_CHAT_MSG,
                    "msg":{"user": player_name, "color": player_color,"str": message["msg"]}
                }
                await game_manager.lobby_broadcast(broadcast, lobby.lobby_id)

    except WebSocketDisconnect:
        await game_manager.disconnect(websocket, lobby.lobby_id)
        await game_manager.lobby_broadcast(await game_manager.get_players(lobby.lobby_id), lobby.lobby_id)
