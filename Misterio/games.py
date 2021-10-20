from fastapi import APIRouter, HTTPException, status, Body
from starlette.responses import Response
import database as db
from pony.orm import db_session, flush, select

game = APIRouter(prefix="/game")

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
		games_query = select(g for g in db.Game if (g.playerCount < 6)).order_by(db.Game.game_id)
		if not games_query.exists():
			response.status_code = status.HTTP_204_NO_CONTENT	
		gamelist = []
		totalGames = len(games_query)
		for g in games_query:
			game = {}
			game['name'] = g.name
			game['id'] = g.game_id
			game['players'] = int(g.playerCount)
			game['host'] = g.host.nickName
			game['password'] = False #We dont have passwords yet
			gamelist.append(game)
	return {'totalGames':totalGames, 'games':gamelist}