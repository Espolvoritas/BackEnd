from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect ,Body
import logging
import asyncio
from typing import List, TypedDict
from starlette.responses import Response

import database as db
from pony.orm import db_session, flush, select

game = APIRouter(prefix="/game")
logger = logging.getLogger("game")

class userConnections(TypedDict):
	websocket: WebSocket
	userID: int

class lobbyConnections(TypedDict):
	lobbyID: int
	websockets: List[WebSocket]

class ConnectionManager:
	def __init__(self):
		self.active_connections: userConnections = {}
		self.active_lobbys: lobbyConnections = {}

	async def connect(self, websocket: WebSocket, userID):
		await websocket.accept()
		self.active_connections[websocket] = userID
		with db_session:
			lobby = db.Player.get(player_id=userID).lobby
			if lobby.game_id not in self.active_lobbys:
				self.active_lobbys[lobby.game_id] = list()
			self.active_lobbys[lobby.game_id].append(websocket)

	def disconnect(self, websocket: WebSocket, lobbyID: int):
		del self.active_connections[websocket]
		self.active_lobbys[lobbyID].remove(websocket)

	async def send_personal_message(self, message: str, websocket: WebSocket):
		await websocket.send_text(message)


	async def broadcast(self, message: str):
		for connection in self.active_connections.keys():
			await connection.send_text(message)

	async def lobby_broadcast(self, message: str, lobbyID: int):
		for connection in self.active_lobbys[lobbyID]:
			await connection.send_text(message)

	async def getPlayers(self, lobbyID: int):
		player_list = []
		for connection in self.active_lobbys[lobbyID]:
			with db_session:
				player = db.Player.get(player_id=self.active_connections[connection])
			if player is None or player.lobby is None:
				await manager.send_personal_message(status.HTTP_400_BAD_REQUEST,connection)
				await connection.close()
				return
			else:
				player_list.append(player.nickName)
		return player_list
		
manager = ConnectionManager()

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
		games_query = select(g for g in db.Game if (g.playerCount < 6)).order_by(db.Game.name)	
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

@game.websocket("/game/getPlayers/{userID}")
async def getPlayers(websocket: WebSocket, userID: int):
	with db_session:
			player = db.Player.get(player_id=userID)
			if player is None or player.lobby is None:
				await websocket.close()
				return
			lobby = player.lobby
	await manager.connect(websocket, userID)
	try:
		await manager.lobby_broadcast(await manager.getPlayers(lobby.game_id), lobby.game_id)
		while True:
			try:
				await asyncio.wait_for(websocket.receive_text(), 0.0001)
			except asyncio.TimeoutError:
				pass
	except WebSocketDisconnect:
		manager.disconnect(websocket, lobby.game_id)
		await manager.lobby_broadcast(await manager.getPlayers(lobby.game_id), lobby.game_id)

@game.post("/getPlayersPost", status_code=status.HTTP_200_OK)
async def getPlayersPost(userID: int = Body(...)):
	with db_session:
		player_list = []
		player = db.Player.get(player_id=userID)
		if player is None and player.lobby is None:
			raise HTTPException(status_code=400, detail="Player does not exist or is not in a lobby")
		current_game = player.lobby
		players_query = select(p for p in current_game.players).order_by(lambda p: p.player_id)
		for player in players_query:
			player_list.append(player.nickName)
		return player_list
