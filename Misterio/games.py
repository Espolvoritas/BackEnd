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

	def exists(self, userID):
		return userID in self.active_connections.values()

	async def connect(self, websocket: WebSocket, userID):
		await websocket.accept()
		self.active_connections[websocket] = userID
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

	async def send_personal_message(self, message: List[str], websocket: WebSocket):
		await websocket.send_json(message)


	async def broadcast(self, message: List[str]):
		for connection in self.active_connections.keys():
			await connection.send_json(message)

	async def lobby_broadcast(self, message: List[str], lobbyID: int):
		if lobbyID in self.active_lobbys.keys():
			for connection in self.active_lobbys[lobbyID]:
				await connection.send_json(message)

	async def getPlayers(self, lobbyID: int):
		player_list = []
		if lobbyID in self.active_lobbys.keys():
			for connection in self.active_lobbys[lobbyID]:
				with db_session:
					player = db.Player.get(player_id=self.active_connections[connection])
				#If we've gotten this far this should never happen, but still
				if player is None or player.lobby is None:
					await connection.close(code=status.WS_1008_POLICY_VIOLATION)
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

@game.websocket("/game/getPlayers/{userID}")
async def getPlayers(websocket: WebSocket, userID: int):
	with db_session:
			player = db.Player.get(player_id=userID)
			if player is None or player.lobby is None or manager.exists(userID):
				await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
				return
			lobby = player.lobby
			isHost = player.hostOf == lobby
	try:
		await manager.connect(websocket, userID)
		await manager.lobby_broadcast(await manager.getPlayers(lobby.game_id), lobby.game_id)
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

@game.post("/startGame", status_code=status.HTTP_200_OK)
async def startGame(userID: int = Body(...)):
	with db_session:
		host = db.Player.get(player_id=userID)
		lobby = host.lobby
		if lobby.host != host:
			raise HTTPException(status_code=403, detail="Only host can start game")
		if lobby is None:
			raise HTTPException(status_code=400, detail="Lobby does not exist")
		if lobby.playerCount < 2:
			raise HTTPException(status_code=405, detail="Not enough players")
		else:
			lobby.isStarted = True
			lobby.sortPlayers()
			await manager.lobby_broadcast("STATUS_GAME_STARTED", lobby.game_id)
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
            return { "nicknameIsValid": False, "playerId": -1, "gameIdIsValid": False }

        if chosenGame is not None and not nicknameIsTaken:

            newPlayer = db.Player(nickName=str(playerNickname))

            flush() # flush so the newPlayer is committed to the database

            chosenGame.addPlayer(newPlayer)
            newPlayerId = newPlayer.player_id

            return { "nicknameIsValid": True, "playerId": newPlayerId, "gameIdIsValid": True }

        else:
            raise HTTPException(status_code=400, detail="Unexpected code reached")
