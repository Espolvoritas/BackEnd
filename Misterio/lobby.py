from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect ,Body
from pony.orm import db_session, flush, select
from starlette.responses import Response
import logging
import asyncio

import Misterio.database as db
import Misterio.manager as mng
from Misterio.functions import *

lobby = APIRouter(prefix="/lobby")
logger = logging.getLogger("lobby")

manager = mng.ConnectionManager()

@lobby.post("/createNew", status_code=status.HTTP_201_CREATED)
async def create_new_game(name: str = Body(...), host: str = Body(...)):
    with db_session:
        if db.Lobby.get(name=name) is not None:
            raise HTTPException(status_code=400, detail="The game name is already in use")
        new_player = db.Player(nickname=host)
        new_game = db.Lobby(name=name, host=new_player, is_started=False)
        flush()
        new_game.add_player(new_player)
        return {"lobby_id": new_game.lobby_id, "player_id": new_player.player_id}


@lobby.get("/availableGames", status_code=status.HTTP_200_OK)
async def get_available_games():
    game_list = []
    with db_session:
        games_query = select(g for g in db.Lobby if ((g.player_count < 6)and not (g.is_started))).order_by(db.Lobby.name)    
        for g in games_query:
            game = {}
            game["name"] = g.name
            game["id"] = g.lobby_id
            game["players"] = int(g.player_count)
            game["host"] = g.host.nickname
            game["password"] = False #We dont have passwords yet
            game_list.append(game)
    if not game_list:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    return game_list


@lobby.post("/startGame", status_code=status.HTTP_200_OK)
async def start_game(player_id: int = Body(...)):
    with db_session:
        host = get_player_by_id(player_id)
        if host is None:
            raise HTTPException(status_code=400, detail=f"Player {player_id} does not exist")
        lobby = host.lobby
        if lobby is None:
            raise HTTPException(status_code=400, detail="Lobby does not exists")    
        if lobby.host != host:
            raise HTTPException(status_code=403, detail="Only host can start game")
        if lobby.player_count < 2:
            raise HTTPException(status_code=405, detail="Not enough players")
        else:
            lobby.game = db.Game(lobby=lobby)
            lobby.is_started = True
            lobby.game.sort_players()
            lobby.game.shuffle_deck()
            lobby.game.set_starting_positions()
            await manager.lobby_broadcast("STATUS_GAME_STARTED", lobby.lobby_id)
    return {}


@lobby.post("/joinCheck", status_code=status.HTTP_200_OK)
async def join_lobby(lobby_id: int = Body(...), player_nickname: str = Body(...)):

    with db_session:
        chosen_lobby = get_lobby_by_id(lobby_id)
        if chosen_lobby is None:
            raise HTTPException(status_code=404, detail="Bad Request")
        existing_nicknames = set([player.nickname for player in select(p for p in chosen_lobby.players)])
        nickname_is_taken = player_nickname in existing_nicknames
        if nickname_is_taken:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already in use")
        if chosen_lobby is not None and not nickname_is_taken:
            new_player = db.Player(nickname=str(player_nickname))
            flush() # flush so the new_player is committed to the database
            chosen_lobby.add_player(new_player)
            new_player_id = new_player.player_id

            return { "nickname_is_valid": True, "player_id": new_player_id, "lobby_id_is_valid": True }

        else:
            raise HTTPException(status_code=400, detail="Unexpected code reached")

@lobby.put("/pickColor")
async def pick_color(player_id: int = Body(...), color: int = Body(...)):
    with db_session:
        player = get_player_by_id(player_id)
        chosen_color = db.Color.get(color_id=color)
        colors = player.lobby.get_available_colors()
        if chosen_color not in colors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Color doesn't exists or is already in use")
        else:
            player.set_color(chosen_color)
            flush()
            await manager.lobby_broadcast(await manager.get_players(player.lobby.lobby_id), player.lobby.lobby_id)


@lobby.websocket("/lobby/{player_id}")
async def handle_lobby(websocket: WebSocket, player_id: int):
    with db_session:
        player = get_player_by_id(player_id)
        if player is None or player.lobby is None or manager.exists(player_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        player_name = get_player_nickname(player_id)
        player_color = get_player_color(player_id)
        lobby = player.lobby
        isHost = player.host_of == lobby
    try:
        await manager.connect(websocket, player_id)
        await manager.lobby_broadcast(await manager.get_players(lobby.lobby_id), lobby.lobby_id)
        while True:
            try:
                await asyncio.wait_for(await websocket.receive_text(), 0.0001)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        if isHost:
            await manager.disconnect_everyone(websocket, lobby.lobby_id)
            await manager.host_disconnect(websocket, lobby.lobby_id)
        else:
            manager.disconnect(websocket, lobby.lobby_id)
            await asyncio.sleep(0.1)
            await manager.lobby_broadcast(await manager.get_players(lobby.lobby_id), lobby.lobby_id)