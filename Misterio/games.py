from fastapi import APIRouter, HTTPException, status, Body

game = APIRouter(prefix="/game")

games = []

class Game:
	def __init__(self, id, name, host):
	  self.id = id
	  self.name = name
	  self.host = host
	  self.players = [host]

@game.post("/createNew", status_code=status.HTTP_201_CREATED)
async def createNewGame(name: str = Body(...), host: str = Body(...)) -> int:
	for x in games:
		if x.name == name:
			raise HTTPException(status_code=400, detail="The game name is already in use")
	ID = len(games)+1
	new_game = Game(ID ,name, host)
	games.append(new_game)
	return ID