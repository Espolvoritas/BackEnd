from fastapi.testclient import TestClient
import string    
import random # define the random module  

from Misterio.server import app

client = TestClient(app)

#aux function for getting random strings
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def test_create_new_game():
    response = client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6), "host": get_random_string(6)}
				)
    assert response.status_code == 201

def test_create_new_game_missing_name():
    response = client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"host": get_random_string(6)}
				)
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'name'], 'msg': 'field required', 
     'type': 'value_error.missing'}]}

def test_create_new_game_missing_host():
    response = client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": get_random_string(6)}
				)
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'host'], 'msg': 'field required', 
     'type': 'value_error.missing'}]}

def test_create_new_game_missing_all():
    response = client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={}
				)
    assert response.status_code == 422
    assert response.json() == {'detail': [{'loc': ['body', 'name'], 'msg': 'field required',
     'type': 'value_error.missing'}, {'loc': ['body', 'host'], 'msg': 'field required', 'type': 
     'value_error.missing'}]}

def test_create_new_game_repeated_name():
    reuse_name = get_random_string(6)
    response = client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": reuse_name, "host": get_random_string(6)}
				)
    assert response.status_code == 201
    #Now do the request with the same game name
    response = client.post("/lobby/createNew",
		headers={"accept": "application/json",
				"Content-Type" : "application/json"},
				json={"name": reuse_name, "host": get_random_string(6)}
				)
    assert response.status_code == 400
    assert response.json() == {'detail': 'The game name is already in use'}
