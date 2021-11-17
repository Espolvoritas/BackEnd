from Misterio import database as database
from pony.orm import db_session, flush, select
from Misterio.functions import get_cell_by_coordinates
from Misterio.server import app
from fastapi.testclient import TestClient 

client = TestClient(app)

def test_cell_creation():

    with db_session:
        cells = select(c for c in database.Cell)
        
        for c in cells:
            print(f"Cell.x: {c.x}, Cell.y: {c.y}, Cell.type: {c.cell_type}")
            print("All neighbors: ")
            neighbors = list(c.get_neighbors()) + list(c.get_free_neighbors())
            print(neighbors)
            for d in neighbors:
                print(d.x, d.y, d.cell_type)

def test_reachability():
    with db_session:
        sampleCell = get_cell_by_coordinates(4, 7)
        reachable = sampleCell.get_reachable(4)
        for cell, distance in list(reachable):
            print(cell.x, cell.y, cell.cell_type, distance)

        sampleCell = get_cell_by_coordinates(12, 7)
        reachable = sampleCell.get_reachable(6)
        for cell, distance in list(reachable):
            print(cell.x, cell.y, cell.cell_type, distance)
   
def test_get_moves():
    with db_session:
        p1 = database.Player(nickname="Mr. Previous")
        p2 = database.Player(nickname="Mr. Next")
        p3 = database.Player(nickname="Mr. Evenafter")

        flush()

        p1.location = get_cell_by_coordinates(4, 7)
        p2.location = get_cell_by_coordinates(4, 7)
        p3.location = get_cell_by_coordinates(16, 7)

        flush()

    response = client.post("/gameBoard/moves",
        headers={"accept": "application/json",
                "Content-Type" : "application/json"},
                json={"player_id": 1, "x": 4, "y": 7, "cost": 4}
                )
                
    responseJson = response.json()
    print(responseJson)
