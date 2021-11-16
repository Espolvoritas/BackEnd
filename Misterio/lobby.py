from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect ,Body
from pony.orm import db_session, flush, select
from starlette.responses import Response
import logging
import asyncio

import Misterio.database as db
import Misterio.manager as mng

game = APIRouter(prefix="/lobby")
logger = logging.getLogger("lobby")

manager = mng.ConnectionManager()

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
			await manager.lobby_broadcast(await manager.getPlayers(lobby.game_id), lobby.game_id)
