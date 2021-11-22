from typing import List, TypedDict
from fastapi import status, WebSocket
from pony.orm import db_session
import Misterio.database as db
from Misterio.functions import get_color_list, get_next_turn
from Misterio.constants import WS_CURR_PLAYER

class userConnections(TypedDict):
    websocket: WebSocket
    player_id: int

class lobbyConnections(TypedDict):
    lobby_id: int
    websockets: List[WebSocket]

class ConnectionManager:
    def __init__(self):
        self.active_connections: userConnections = {}
        self.active_lobbys: lobbyConnections = {}

    def exists(self, player_id):
        return player_id in self.active_connections.values()

    def get_websocket(self, player_id):
        key_list = list(self.active_connections.keys())
        val_list = list(self.active_connections.values())
        position = val_list.index(player_id)
        return key_list[position]

    async def connect(self, websocket: WebSocket, player_id):
        await websocket.accept()
        self.active_connections[websocket] = player_id
        with db_session:
            lobby = db.Player.get(player_id=player_id).lobby
            if lobby.lobby_id not in self.active_lobbys:
                self.active_lobbys[lobby.lobby_id] = list()
            self.active_lobbys[lobby.lobby_id].append(websocket)

    async def disconnect_everyone(self, websocket: WebSocket,lobby_id: int):
        connections = self.active_lobbys[lobby_id].copy()
        for connection in connections:
            if connection != websocket:
                await connection.close(code=status.WS_1001_GOING_AWAY)

    async def host_disconnect(self, websocket: WebSocket, lobby_id: int):
        if websocket in self.active_connections.keys():
            player_id = self.active_connections[websocket]
            del self.active_connections[websocket]
            self.active_lobbys[lobby_id].remove(websocket)
            with db_session(optimistic=False):
                game = db.Lobby.get(lobby_id=lobby_id)
                if game is not None:
                    if not game.is_started:
                        game.delete()
                        db.Player.get(player_id=player_id).delete()

    def disconnect(self, websocket: WebSocket, lobby_id: int):
        if websocket in self.active_connections.keys():
            player_id = self.active_connections[websocket]
            del self.active_connections[websocket]
            self.active_lobbys[lobby_id].remove(websocket)
            with db_session(optimistic=False):
                game = db.Lobby.get(lobby_id=lobby_id)
                if game is not None:
                    if not game.is_started:
                        db.Player.get(player_id=player_id).delete()
                        game.player_count -= 1

    def get_websocket(self, player_id: int, lobby_id):
        if lobby_id in self.active_lobbys.keys():
            for connection in self.active_lobbys[lobby_id]:
                if self.active_connections[connection] == player_id:
                    return connection

    async def send_personal_message(self, message: List[str], websocket: WebSocket):
        await websocket.send_json(message)


    async def broadcast(self, message: List[str]):
        for connection in self.active_connections.keys():
            await connection.send_json(message)

    async def lobby_broadcast(self, message: List[str], lobby_id: int):
        if lobby_id in self.active_lobbys.keys():
            for connection in self.active_lobbys[lobby_id]:
                await connection.send_json(message)

    async def almost_lobby_broadcast(self, message: List[str], websockets: list, lobby_id: int):
        if lobby_id in self.active_lobbys.keys():
            for connection in self.active_lobbys[lobby_id]:
                if not connection in websockets:
                    await connection.send_json(message)

    async def get_players(self, lobby_id: int):
        player_list = []
        colors = get_color_list(lobby_id)
        response = {}
        if lobby_id in self.active_lobbys.keys():
            for connection in self.active_lobbys[lobby_id]:
                with db_session:
                    player = db.Player.get(player_id=self.active_connections[connection])
                #If we"ve gotten this far this should never happen, but still
                if player is None or player.lobby is None:
                    await connection.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
                else:
                    playerjson = {}
                    playerjson["nickname"] = player.nickname
                    playerjson["Color"] = player.color.color_id
                    player_list.append(playerjson)
        response["colors"] = colors
        response["players"] = player_list
        return response
    
class GameBoardManager(ConnectionManager):
    picked_card_id = None 

    async def disconnect(self, websocket: WebSocket, lobby_id: int):
        if websocket in self.active_connections.keys():
            player_id = self.active_connections[websocket]
            del self.active_connections[websocket]
            self.active_lobbys[lobby_id].remove(websocket)
            await sleep(DISCONNECT_TIMER)
            if self.get_websocket(player_id, lobby_id) is None:
                set_afk(player_id,True)
    async def update_turn(self, lobby_id: int):
        await self.lobby_broadcast({"code": WS_CURR_PLAYER, "current_player": get_next_turn(lobby_id)}, lobby_id)
        