from fastapi import APIRouter, HTTPException, status, Body
import database as db
from pony.orm import db_session, flush

game = APIRouter(prefix="/game")

@game.post("/createNew", status_code=status.HTTP_201_CREATED)
async def createNewGame(name: str = Body(...), host: str = Body(...)) -> int:
	with db_session:
		if db.Game.get(name=name) is not None:
			raise HTTPException(status_code=400, detail="The game name is already in use")
		new_player = db.Player(nickName=host)
		new_game = db.Game(name=name, host=new_player, isStarted=False)
		flush()
		new_game.addPlayer(new_player)
		return new_game.game_id