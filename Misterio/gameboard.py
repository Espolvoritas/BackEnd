from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, HTTPException, Body
from pony.orm import db_session, select
from asyncio import sleep

import Misterio.database as db
from Misterio.constants import *
from Misterio.lobby import ConnectionManager
from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, Body
from pony.orm import db_session
from pony.orm import get as dbget

class GameBoardManager(ConnectionManager):
	pickedCard_id = None 
		
gameBoard = APIRouter(prefix="/gameBoard")

gameBoard_manager = GameBoardManager()

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

@gameBoard.websocket("/gameBoard/{userID}")
async def handleTurn(websocket: WebSocket, userID: int):
	
	with db_session:
		player = db.Player.get(player_id=userID)
		if player is None or player.lobby is None or gameBoard_manager.exists(userID):
			await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
			return
		lobby = player.lobby
		await gameBoard_manager.connect(websocket, userID)
		await gameBoard_manager.send_personal_message({"code" : WS_CURR_PLAYER + WS_CARD_LIST ,
			"currentPlayer" : lobby.currentPlayer.nickName, "cards" : get_card_list(userID)}, websocket)

	try:
		await gameBoard_manager.connect(websocket, userID)
		await gameBoard_manager.send_personal_message(responseMessage, websocket)
		while(True):
			message = await websocket.receive_json()
			
			gameBoard_manager.pickedCard_id = message['card']
			await gameBoard_manager.lobby_broadcast({"code" : WS_CURR_PLAYER, "currentPlayer" : get_next_turn(lobby.game_id)}, lobby.game_id)
	except WebSocketDisconnect:
		gameBoard_manager.disconnect(websocket, lobby.game_id)
		await gameBoard_manager.lobby_broadcast(await gameBoard_manager.getPlayers(lobby.game_id), lobby.game_id)

@gameBoard.post("/rollDice", status_code=status.HTTP_200_OK)
async def rollDice(playerId: int = Body(...), roll: int = Body(...)):
	if player_in_turn(playerId):
		with db_session:
			player = db.Player.get(player_id=playerId)
			player.currentDiceRoll = int(roll)
	else:
		raise HTTPException(status_code=403, detail="Player can't roll dice outside his/her turn.")
	await gameBoard_manager.lobby_broadcast({"code" : WS_CURR_PLAYER, "currentPlayer" : get_next_turn(player.lobby.game_id)}, player.lobby.game_id)


@gameBoard.post("/checkSuspicion", status_code=status.HTTP_200_OK)
async def check_suspicion(playerId: int = Body(...), victimId: int = Body(...), culpritId: int = Body(...)):
	with db_session:
		player = db.Player.get(player_id=playerId)
		lobby = player.lobby
		victim = db.Card.get(cardId=victimId)
		culprit = db.Card.get(cardId=culpritId)
		if player is None:
			raise HTTPException(status_code=400, detail="Player does not exist")
		if lobby is None:
			raise HTTPException(status_code=403, detail="Player is not in game.")
		if lobby.currentPlayer != player:
			raise HTTPException(status_code=403, detail="Player can't make a suspicion outside his/her turn.")
		if (not player.inRoom):
			raise HTTPException(status_code=403, detail="Player must be in a room to make a suspicion.")
		if (victim.cardType != "Victim" or culprit.cardType != "Monster"):
			raise HTTPException(status_code=403, detail="Suspicion card types are invalid.")
		else:
			roomName = player.location.roomName
			roomId = select(c.cardId for c in db.Card if c.cardName == roomName).first()
			players = []
			currplayerId = player.nextPlayer.player_id
			for i in range(lobby.playerCount):
				currplayer = db.Player.get(player_id=currplayerId)
				currplayerCards = [c.cardId for c in currplayer.cards]
				players.append([currplayer.player_id, currplayerCards])
				currplayerId = currplayer.nextPlayer.player_id
			players.reverse()
			suspicion = [culpritId, victimId, roomId]
	suspicionCard = await checkSuspicion_players(players, suspicion, lobby.game_id)
	return {'status': 'SUSPICION_RESPONDED', 'args': [suspicionCard]}

async def checkSuspicion_players(players: list, suspicion: list, lobbyId: int):
	responded = False
	while (not responded or not players):
		nextPlayer = players.pop()
		matches = []
		for card in suspicion:
			if card in nextPlayer[1]:
				matches.append(card)
		if matches:
			if len(matches) > 1:
				responseMessage = {'status': 'PICK_CARD', 'args': matches}
				websocket = gameBoard_manager.get_websocket(nextPlayer[0], lobbyId)
				#Send next player the option to pick a card
				await gameBoard_manager.send_personal_message(responseMessage, websocket)
				while gameBoard_manager.pickedCard_id is None:
					#Await for next player to pick a card to show (maybe implement timer)
					await sleep(1)
				suspicionCard = gameBoard_manager.pickedCard_id
				gameBoard_manager.pickedCard_id = None
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
