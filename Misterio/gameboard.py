from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, HTTPException, Body
from pony.orm import db_session, select
from asyncio import sleep
import logging
import Misterio.database as db
from Misterio.constants import *
from Misterio.lobby import ConnectionManager
from fastapi import APIRouter, status, WebSocket, WebSocketDisconnect, Body
from pony.orm import db_session
from pony.orm import get as dbget
from starlette.responses import Response

class GameBoardManager(ConnectionManager):
	pickedCard_id = None 
		
gameBoard = APIRouter(prefix="/gameBoard")
logger = logging.getLogger("gameboard")

gameBoard_manager = GameBoardManager()

#crashes if position is not valid
def cellByCoordinates(x, y):
	return dbget(c for c in db.Cell if c.x == x and c.y == y)

@db_session
def positionList(lobbyID):
	positionList = []
	game = db.Game.get(game_id=lobbyID)
	for player in list(game.players):
		positionList.append({"player_id": player.player_id, "color": player.color.color_id ,"x" : player.location.y, "y": player.location.x})
	return positionList

@db_session
def getReachable(player_id):
	moves = []
	player = db.Player.get(player_id=player_id)
	reachableCells = player.location.getReachable(player.currentDiceRoll)
	if reachableCells is not None:
		for cell, distance in reachableCells:
			option = {"x": 0, "y": 0, "remaining": 0}
			#Inverted because keep logic working
			option["x"] = cell.y
			option["y"] = cell.x
			option["remaining"] = distance
			moves.append(option)
	return moves

#todo check cost < roll and check newPosition is in movement range
@gameBoard.post("/moves", status_code=status.HTTP_200_OK)
async def get_moves(player_id: int = Body(...), x: int = Body(...), y: int = Body(...), remaining: int = Body(...)):
	room = None
	with db_session:
		player = db.Player.get(player_id=player_id)
		newPosition = cellByCoordinates(x, y)
		if not newPosition or player != player.lobby.currentPlayer:
			raise HTTPException(status.HTTP_400_BAD_REQUEST)
		if newPosition.cellType == "room":
			room = getRoomID(newPosition.roomName)
			player.currentDiceRoll = 0
		else:
			player.currentDiceRoll = remaining
		if room is None and remaining == 0:
			await update_turn(player.lobby.game_id)
		player.location = newPosition
	await gameBoard_manager.lobby_broadcast({"code": WS_POS_LIST + WS_ROOM,"positions":positionList(player.lobby.game_id), "room": room}, player.lobby.game_id)
	return {"moves" : getReachable(player_id)}

def getRoomID(roomName: str):
	for room in db.Room:
		if room.name == roomName:
			return room.value

async def update_turn(lobbyID: int):
	await gameBoard_manager.lobby_broadcast({"code": WS_CURR_PLAYER, "currentPlayer": get_next_turn(lobbyID)}, lobbyID)

@db_session
def get_next_turn(lobbyID: int):
	lobby = db.Game.get(game_id=lobbyID)
	currentPlayer = lobby.currentPlayer
	lobby.currentPlayer = currentPlayer.nextPlayer
	return lobby.currentPlayer.nickName

@db_session
def get_current_turn(lobbyID: int):
	lobby = db.Game.get(game_id=lobbyID)
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
		await gameBoard_manager.send_personal_message({"code" : WS_CURR_PLAYER + WS_CARD_LIST +  
		WS_POS_LIST, "currentPlayer" : get_current_turn(lobby.game_id), "cards" : get_card_list(userID), 
		"positions" : positionList(lobby.game_id)}, websocket)

	try:
		while(True):
			message = await websocket.receive_json()
			
			gameBoard_manager.pickedCard_id = message['card']
			await gameBoard_manager.lobby_broadcast({"code" : WS_CURR_PLAYER, "currentPlayer" : get_current_turn(lobby.game_id)}, lobby.game_id)
	except WebSocketDisconnect:
		gameBoard_manager.disconnect(websocket, lobby.game_id)
		await gameBoard_manager.lobby_broadcast(await gameBoard_manager.getPlayers(lobby.game_id), lobby.game_id)

@gameBoard.post("/rollDice", status_code=status.HTTP_200_OK)
async def rollDice(playerId: int = Body(...), roll: int = Body(...)):
	if player_in_turn(playerId):
		with db_session:
			player = db.Player.get(player_id=playerId)
			player.currentDiceRoll = int(roll)
			await gameBoard_manager.send_personal_message({"code" : WS_AVAIL_MOVES, "moves" : getReachable(playerId)}, gameBoard_manager.getWebsocket(playerId))
	else:
		raise HTTPException(status_code=403, detail="Player can't roll dice outside his/her turn.")


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
			player.currentDiceRoll = 0
			for i in range(lobby.playerCount):
				currplayer = db.Player.get(player_id=currplayerId)
				currplayerCards = [c.cardId for c in currplayer.cards]
				players.append([currplayer.player_id, currplayer.nickName, currplayerCards])
				currplayerId = currplayer.nextPlayer.player_id
			players.reverse()
			suspicion = [culpritId, victimId, roomId]
	await gameBoard_manager.lobby_broadcast({'code': WS_SUSPICION, 'victim': victimId, 'culprit': culpritId, 'room': roomId}, lobby.game_id)
	suspicionCard = await checkSuspicion_players(players, player.nickName, suspicion, lobby.game_id)
	return {'status': 'SUSPICION_RESPONDED', 'suspicionCard': suspicionCard}

async def checkSuspicion_players(players: list, playerInTurn: str, suspicion: list, lobbyId: int):
	responded = False
	while (not responded or not players):
		nextPlayer = players.pop()
		matches = []
		for card in suspicion:
			if card in nextPlayer[2]:
				matches.append(card)
		if matches:
			if len(matches) > 1:
				responseMessage = {'status': 'PICK_CARD', 'args': matches}
			websocket = gameBoard_manager.get_websocket(nextPlayer[0], lobbyId)
			if len(matches) > 1:
				responseMessage = {'code': WS_PICK_CARD, 'matchingCards': matches}
				#Send next player the option to pick a card
				await gameBoard_manager.send_personal_message(responseMessage, websocket)
				while gameBoard_manager.pickedCard_id is None:
					#Await for next player to pick a card to show (maybe implement timer)
					await sleep(1)
				suspicionCard = gameBoard_manager.pickedCard_id
				gameBoard_manager.pickedCard_id = None
			else:
				suspicionCard = matches.pop()
				responseMessage = {'code': WS_SUSPICION_NOTIFY, 'playerInTurn': playerInTurn, 'card': suspicionCard}
				await gameBoard_manager.send_personal_message(responseMessage, websocket)
			responded = True
		responseBroadcast = {'code': WS_SUSPICION_STATUS , 'responded': responded, 'player': nextPlayer[1]}
		#Broadcast suspicion status to all players
		await gameBoard_manager.lobby_broadcast(responseBroadcast, lobbyId)
	
	responseMessage = {'status': 'SUSPICION_RESPONDED', 'args': [suspicionCard]}
	return responseMessage