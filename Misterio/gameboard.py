from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect
from pony.orm import db_session

import Misterio.database as db
from Misterio.lobby import ConnectionManager

gameBoard = APIRouter(prefix="/gameBoard")

gameBoard_manager = ConnectionManager()

@db_session
def get_next_turn(lobbyID: int):
	lobby = db.Game.get(game_id=lobbyID)
	currentPlayer = lobby.currentPlayer
	lobby.currentPlayer = currentPlayer.nextPlayer
	return lobby.currentPlayer.nickName

@db_session
def player_in_turn(userID: int):
	player = db.Player.get(player_id=userID)
	lobby = player.lobby
	return userID == lobby.currentPlayer.player_id

@db_session
def get_card_list(userID: int):
	cards = list(db.Player.get(player_id=userID).cards)
	return list(c.cardId for c in cards)

@gameBoard.websocket("/gameBoard/{userID}")
async def handleTurn(websocket: WebSocket, userID: int):
	await gameBoard_manager.connect(websocket, userID)
	with db_session:
		player = db.Player.get(player_id=userID)
		lobby = player.lobby
		await gameBoard_manager.send_personal_message({"currentPlayer" : lobby.currentPlayer.nickName,
		"cards" : get_card_list(userID)}, websocket)
	try:
		while(True):
			roll = await websocket.receive_text()
			if player_in_turn(userID):
				with db_session:
					player = db.Player.get(player_id=userID)
					player.currentDiceRoll = int(roll)
				await gameBoard_manager.lobby_broadcast(get_next_turn(lobby.game_id), lobby.game_id)
	except WebSocketDisconnect:
		gameBoard_manager.disconnect(websocket, lobby.game_id)
		await gameBoard_manager.lobby_broadcast(await gameBoard_manager.getPlayers(lobby.game_id), lobby.game_id)