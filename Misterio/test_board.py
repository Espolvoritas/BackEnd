import database
from pony.orm import db_session, flush, select
from turns import cellByCoordinates
from server import app
from fastapi.testclient import TestClient 

client = TestClient(app)

def test_cell_creation():

    with db_session:
        cells = select(c for c in database.Cell)
        
        for c in cells:
            print(f"Cell.x: {c.x}, Cell.y: {c.y}, Cell.type: {c.cellType}")
            print("All neighbors: ")
            neighbors = list(c.getNeighbors()) + list(c.getFreeNeighbors())
            print(neighbors)
            for d in neighbors:
                print(d.x, d.y, d.cellType)

def test_reachability():
    with db_session:
        sampleCell = cellByCoordinates(4, 7)
        reachable = sampleCell.getReachable(4)
        for cell, distance in list(reachable):
            print(cell.x, cell.y, cell.cellType, distance)

        sampleCell = cellByCoordinates(12, 7)
        reachable = sampleCell.getReachable(6)
        for cell, distance in list(reachable):
            print(cell.x, cell.y, cell.cellType, distance)
   
def test_get_moves():
    with db_session:
        p1 = database.Player(nickName="Mr. Previous")
        p2 = database.Player(nickName="Mr. Next")
        p3 = database.Player(nickName="Mr. Evenafter")

        flush()

        p1.location = cellByCoordinates(4, 7)
        p2.location = cellByCoordinates(4, 7)
        p3.location = cellByCoordinates(16, 7)

        flush()

    response = client.post("/gameBoard/moves",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"player_id": 1, "x": 4, "y": 7, "cost": 4}
				)
                
    responseJson = response.json()
    print(responseJson)
