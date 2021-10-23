from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect
import database as db
from pony.orm import db_session
from games import ConnectionManager
import logging
import asyncio
from time import sleep

gameBoard = APIRouter(prefix="/gameBoard")

gameBoard_manager = ConnectionManager()

@gameBoard.websocket("/game/startGame")
async def startGame(websocket: WebSocket, gameID: int):
	with db_session:
		game = db.Game.get(game_id=gameID)
		if game is None:
			await gameBoard_manager.send_personal_message(status.HTTP_400_BAD_REQUEST,websocket)
			await websocket.close()
			return
		if game.playerCount < 2:
			await gameBoard_manager.send_personal_message(status.HTTP_405_METHOD_NOT_ALLOWED,websocket)
		else:
			game.isStarted = True
			game.sortPlayers()

logger = logging.getLogger("gameBoard")

def update_roll(userID, diceRoll):
	print("UPDATED ROLL")
	with db_session:
		player = db.Player.get(player_id=userID)
		player.currentDiceRoll = int(diceRoll)
	

def check_in_turn(userID):
	with db_session:
		player = db.Player.get(player_id=userID)
		lobby = player.lobby
		lobby.sortPlayers()
		playerInTurn = userID == lobby.currentPlayer.player_id
	try:
		while(True):
			roll = await websocket.receive_text()
			if playerInTurn:
				with db_session:
					player = db.Player.get(player_id=userID)
					player.currentDiceRoll = int(roll)
				playerInTurn = False
	except WebSocketDisconnect:
		gameBoard_manager.disconnect(websocket, lobby.game_id)
			print("Exception handled")
		await gameBoard_manager.lobby_broadcast(await gameBoard_manager.getPlayers(lobby.game_id), lobby.game_id)
		try:
			await asyncio.wait_for(websocket.receive_text(), 0.0001)
		except asyncio.TimeoutError:
			pass

				