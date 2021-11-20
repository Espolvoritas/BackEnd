from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect ,Body
from pony.orm import db_session, flush, select
from typing import List, TypedDict
from starlette.requests import cookie_parser
from starlette.responses import Response
import logging
import asyncio

import Misterio.database as db

MSG_PERIOD=0.2

game = APIRouter(prefix="/lobby")
logger = logging.getLogger("lobby")

class msgBuffer(TypedDict):
	userID: int
	buffer: List[dict]
class userConnections(TypedDict):
	websocket: WebSocket
	userID: int

class lobbyConnections(TypedDict):
	lobbyID: int
	websockets: List[WebSocket]

class ConnectionManager:
	def __init__(self):
		self.buffer: msgBuffer = {}
		self.active_connections: userConnections = {}
		self.active_lobbys: lobbyConnections = {}

	def exists(self, userID):
		return userID in self.active_connections.values()

	def getWebsocket(self, userID):
		key_list = list(self.active_connections.keys())
		val_list = list(self.active_connections.values())
		position = val_list.index(userID)
		return key_list[position]

	async def connect(self, websocket: WebSocket, userID):
		await websocket.accept()
		self.active_connections[websocket] = userID
		self.buffer[userID] = {"code": 0}
		with db_session:
			lobby = db.Player.get(player_id=userID).lobby
			if lobby.game_id not in self.active_lobbys:
				self.active_lobbys[lobby.game_id] = list()
			self.active_lobbys[lobby.game_id].append(websocket)

	async def disconnect_everyone(self, websocket: WebSocket,lobbyID: int):
		connections = self.active_lobbys[lobbyID].copy()
		for connection in connections:
			if connection != websocket:
				await connection.close(code=status.WS_1001_GOING_AWAY)

	async def host_disconnect(self, websocket: WebSocket, lobbyID: int):
		if websocket in self.active_connections.keys():
			userID = self.active_connections[websocket]
			del self.active_connections[websocket]
			del self.buffer[userID]
			self.active_lobbys[lobbyID].remove(websocket)
			with db_session(optimistic=False):
				game = db.Game.get(game_id=lobbyID)
				if game is not None:
					if not game.isStarted:
						game.delete()
						db.Player.get(player_id=userID).delete()

	def disconnect(self, websocket: WebSocket, lobbyID: int):
		if websocket in self.active_connections.keys():
			userID = self.active_connections[websocket]
			del self.active_connections[websocket]
			self.active_lobbys[lobbyID].remove(websocket)
			with db_session(optimistic=False):
				game = db.Game.get(game_id=lobbyID)
				if game is not None:
					if not game.isStarted:
						db.Player.get(player_id=userID).delete()
						game.playerCount -= 1

	def get_websocket(self, playerId: int, lobbyId):
		if lobbyId in self.active_lobbys.keys():
			for connection in self.active_lobbys[lobbyId]:
				if self.active_connections[connection] == playerId:
					return connection

	async def empty_buffer(self, websocket):
		while True:
			userID = self.active_connections[websocket]
			if self.buffer[userID]["code"] != 0:
				await websocket.send_json(self.buffer[userID])
				self.buffer[userID] = {"code": 0}
			await asyncio.sleep(MSG_PERIOD)

	async def send_personal_message(self, message: List[dict], websocket: WebSocket, priority=False):
		if not priority:
			userID = self.active_connections[websocket]
			previosCode = self.buffer[userID]["code"]
			self.buffer[userID].update(message)
			if not (previosCode & message["code"]):
				self.buffer[userID]["code"] = previosCode + message["code"]
		else:
			await websocket.send_json(message)


	async def broadcast(self, message: List[str], priority=False):
		for connection in self.active_connections.keys():
			await self.send_personal_message(message, connection, priority)

	async def lobby_broadcast(self, message: List[str], lobbyID: int, priority=False):
		if lobbyID in self.active_lobbys.keys():
			for connection in self.active_lobbys[lobbyID]:
				await self.send_personal_message(message, connection, priority)

	async def almost_lobby_broadcast(self, message: List[str], websocket: WebSocket,lobbyID: int, priority=False):
		if lobbyID in self.active_lobbys.keys():
			for connection in self.active_lobbys[lobbyID]:
				if websocket != connection:
					await self.send_personal_message(message, connection, priority)

	async def getPlayers(self, lobbyID: int):
		player_list = []
		colors = get_colors(lobbyID)
		response = {}
		if lobbyID in self.active_lobbys.keys():
			for connection in self.active_lobbys[lobbyID]:
				with db_session:
					player = db.Player.get(player_id=self.active_connections[connection])
				#If we've gotten this far this should never happen, but still
				if player is None or player.lobby is None:
					await connection.close(code=status.WS_1008_POLICY_VIOLATION)
					return
				else:
					playerjson = {}
					playerjson["nickName"] = player.nickName
					playerjson["Color"] = player.color.color_id
					player_list.append(playerjson)
		response['colors'] = colors
		response['players'] = player_list
		return response
		
manager = ConnectionManager()

def get_colors(gameId):
	color_list = []
	with db_session:
		lobby = db.Game.get(game_id=gameId)
		if lobby:
			color_query = lobby.getAvailableColors()
			for c in color_query:
				color_list.append(c.color_id)
	return color_list

@game.post("/createNew", status_code=status.HTTP_201_CREATED)
async def createNewGame(name: str = Body(...), host: str = Body(...)):
    with db_session:
        if db.Game.get(name=name) is not None:
            raise HTTPException(status_code=400, detail="The game name is already in use")
        new_player = db.Player(nickName=host)
        new_game = db.Game(name=name, host=new_player, isStarted=False)
        flush()
        new_game.addPlayer(new_player)
        return {"game_id": new_game.game_id, "player_id": new_player.player_id}

@game.get("/availableGames", status_code=status.HTTP_200_OK)
async def getAvailableGames():
    gamelist = []
    with db_session:
        games_query = select(g for g in db.Game if ((g.playerCount < 6)and not (g.isStarted))).order_by(db.Game.name)    
        for g in games_query:
            game = {}
            game["name"] = g.name
            game["id"] = g.game_id
            game["players"] = int(g.playerCount)
            game["host"] = g.host.nickName
            game["password"] = False #We dont have passwords yet
            gamelist.append(game)
    if not gamelist:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    return gamelist

@game.websocket("/lobby/{userID}")
async def handleLobby(websocket: WebSocket, userID: int):
	with db_session:
			player = db.Player.get(player_id=userID)
			if player is None or player.lobby is None or manager.exists(userID):
				await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
				return
			lobby = player.lobby
			isHost = player.hostOf == lobby
	task = None
	try:
		task = asyncio.create_task(manager.empty_buffer(websocket))
		await manager.connect(websocket, userID)
		await manager.lobby_broadcast({"code" : 4096, "data" :await manager.getPlayers(lobby.game_id)}, lobby.game_id)
		while True:
			try:
				await asyncio.wait_for(await websocket.receive_text(), 0.0001)
			except asyncio.TimeoutError:
				pass
	except WebSocketDisconnect:
		if isHost:
			await manager.disconnect_everyone(websocket, lobby.game_id)
			await manager.host_disconnect(websocket, lobby.game_id)
		else:
			manager.disconnect(websocket, lobby.game_id)
			await asyncio.sleep(0.1)
			await manager.lobby_broadcast({"code" : 4096, "data" :await manager.getPlayers(lobby.game_id)}, lobby.game_id)
		task.cancel()

@game.post("/startGame", status_code=status.HTTP_200_OK)
async def startGame(userID: int = Body(...)):
	with db_session:
		host = db.Player.get(player_id=userID)
		lobby = host.lobby
		if lobby is None:
			raise HTTPException(status_code=400, detail="Lobby does not exists")	
		if lobby.host != host:
			raise HTTPException(status_code=403, detail="Only host can start game")
		if lobby.playerCount < 2:
			raise HTTPException(status_code=405, detail="Not enough players")
		else:
			lobby.isStarted = True
			lobby.sortPlayers()
			lobby.shuffleDeck()
			lobby.setStartingPositions()
			await manager.lobby_broadcast({"code": 8192}, lobby.game_id, True)
	return {}

@game.post("/joinCheck", status_code=status.HTTP_200_OK)
async def joinGame(gameId: int = Body(...), playerNickname: str = Body(...)):

    with db_session:
        chosenGame = db.Game.get(game_id=gameId)

        if chosenGame is None:
            raise HTTPException(status_code=404, detail="Bad Request")

        existingNicknames = set([player.nickName for player in select(p for p in chosenGame.players)])
        nicknameIsTaken = playerNickname in existingNicknames

        if nicknameIsTaken:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already in use")

        if chosenGame is not None and not nicknameIsTaken:

            newPlayer = db.Player(nickName=str(playerNickname))

            flush() # flush so the newPlayer is committed to the database

            chosenGame.addPlayer(newPlayer)
            newPlayerId = newPlayer.player_id

            return { "nicknameIsValid": True, "playerId": newPlayerId, "gameIdIsValid": True }

        else:
            raise HTTPException(status_code=400, detail="Unexpected code reached")

@game.put("/pickColor")
async def pickColor(player_id: int = Body(...), color: int = Body(...)):
	with db_session:
		player = db.Player.get(player_id=player_id)
		lobby = db.Game.get(game_id=player.lobby.game_id)
		chosen_color = db.Color.get(color_id=color)
		colors = lobby.getAvailableColors()
		if chosen_color not in colors:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Color doesn't exists or is already in use")
		else:
			player.setColor(chosen_color)
			flush()
			await manager.lobby_broadcast({"code" : 4096, "data" :await manager.getPlayers(lobby.game_id)}, lobby.game_id)
