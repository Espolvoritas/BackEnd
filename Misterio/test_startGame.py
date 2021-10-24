from server import app
from fastapi.testclient import TestClient
import string    
import random # define the random module  
import database as db
client = TestClient(app)

def clear_tables():
    db.db.drop_table(db.Player, if_exists=True, with_all_data=True)
    db.db.drop_table(db.Game, if_exists=True, with_all_data=True)
    
    db.db.create_tables()


#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def test_start_game():
	clear_tables()
	response = client.post("/game/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": get_random_string(6)}
				)
	assert response.status_code == 201
	response = client.post("/game/startGame",
				headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"userID": 1, "gameID": 1}
				)
	print(response)
	assert response.status_code == 200


test_start_game()