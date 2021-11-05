from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, HTTPException
from pony.orm import db_session, select

import Misterio.database as db
from Misterio.constants import *
from Misterio.lobby import ConnectionManager
from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, Body
from pony.orm import db_session
from pony.orm import get as dbget

gameBoard = APIRouter(prefix="/gameBoard")

gameBoard_manager = ConnectionManager()

def cellByCoordinates(x, y):
	return dbget(c for c in db.Cell if c.x == x and c.y == y)

@gameBoard.post("/moves", status_code=status.HTTP_201_CREATED)
def get_moves(player_id: int = Body(...), x: int = Body(...), y: int = Body(...), cost: int = Body(...)):
	moves = {"player_id": player_id, "options": []}
	with db_session:
		reachableCells = cellByCoordinates(x, y).getReachable(cost)

		for cell, distance in reachableCells:
			option = {"x": 0, "y": 0, "cost": 0}
			option["x"] = cell.y
			option["y"] = cell.x
			option["cost"] = distance
			moves["options"].append(option)

		return moves

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

async def check_suspicion(playerId: int, suspicion):
	suspicion = list(map(int, suspicion))
	with db_session:
		player = db.Player.get(player_id=playerId)
		if player is None:
			raise HTTPException(status_code=400, detail="Player does not exist")

		lobby = player.lobby
		if lobby is None:
			raise HTTPException(status_code=403, detail="Player is not in game.")
		if lobby.currentPlayer != player:
			raise HTTPException(status_code=403, detail="Player can't make a suspicion outside his/her turn.")
		if (not player.inRoom):
			raise HTTPException(status_code=403, detail="Player must be in a room to make a suspicion.")
		if (suspicion is None or len(suspicion) != 2):
			raise HTTPException(status_code=403, detail="Suspicion must contain two cards.")
		else:
			roomName = player.location.roomName
			roomCard = select(c.cardId for c in db.Card if c.cardName == roomName)
			suspicion.append(roomCard.first())
			players = []
			currplayerId = player.nextPlayer.player_id
			for i in range(lobby.playerCount):
				currplayer = db.Player.get(player_id=currplayerId)
				currplayerCards = [c.cardId for c in currplayer.cards]
				players.append([currplayer.player_id, currplayerCards])
				currplayerId = currplayer.nextPlayer.player_id
	players.reverse()
	responded = False
	while (not responded or not players):
		nextPlayer = players.pop()
		matches = []
		for card in suspicion:
			if card in nextPlayer[1]:
				matches.append(card)
		print("Player beeing suspiced: ", nextPlayer[0], "Suspicion ", suspicion, "Cards: ", nextPlayer[1], "Matches: ", matches)
		if matches:
			if len(matches) > 1:
				responseMessage = {'status': 'PICK_CARD', 'args': matches}
				websocket = gameBoard_manager.get_websocket(nextPlayer[0], lobby.game_id)
				#Send next player the option to pick a card
				await gameBoard_manager.send_personal_message(responseMessage, websocket)
				responseData = None
				while responseData is None:
					#Await for next player to pick a card to show (maybe implement timer)
					responseData = await websocket.receive_json()
					if responseData['status'] == 'PICK_CARD':
						suspicionCard = responseData['args'].pop()
					print("CHOICE RECEIVED: ", suspicionCard)
			else:
				suspicionCard = matches.pop()
			responded = True
		responseBroadcast = {'status': 'SUSPICION_BROADCAST', 'args': [responded, nextPlayer[0]]}
		#Broadcast suspicion status to all players
		await gameBoard_manager.lobby_broadcast(responseBroadcast, lobby.game_id)
	
	responseMessage = {'status': 'SUSPICION_RESPONDED', 'args': [suspicionCard]}
	return responseMessage


@gameBoard.websocket("/gameBoard/{userID}")
async def handleTurn(websocket: WebSocket, userID: int):
	await gameBoard_manager.connect(websocket, userID)
	with db_session:
		player = db.Player.get(player_id=userID)
		lobby = player.lobby
		responseMessage = {'status':'PLAYERINTURN', 'args':[lobby.currentPlayer.nickName]}
		await gameBoard_manager.send_personal_message(responseMessage, websocket)
	try:
		while(True):
			message = await websocket.receive_json()

			if message['status'] == 'SUSPICION':
				suspicion = message['args']
				suspicionResponse = await check_suspicion(userID, suspicion)
				await gameBoard_manager.send_personal_message(suspicionResponse, websocket)
				responseMessage = {'status':'PLAYERINTURN', 'args':[get_next_turn(lobby.game_id)]}
				await gameBoard_manager.lobby_broadcast(responseMessage, lobby.game_id)

			if message['status'] == 'DICEROLL':
				roll = message['args'].pop()
				if player_in_turn(userID):
					with db_session:
						player = db.Player.get(player_id=userID)
						player.currentDiceRoll = int(roll)
				responseMessage = {'status':'PLAYERINTURN', 'args':[get_next_turn(lobby.game_id)]}
				await gameBoard_manager.lobby_broadcast(responseMessage, lobby.game_id)
	except WebSocketDisconnect:
		gameBoard_manager.disconnect(websocket, lobby.game_id)
		await gameBoard_manager.lobby_broadcast(await gameBoard_manager.getPlayers(lobby.game_id), lobby.game_id)
