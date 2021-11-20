from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Misterio.lobby import lobby
from Misterio.gameboard import gameBoard

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lobby)
app.include_router(gameBoard)

@app.get("/")
async def get():
    return {"status": "Server start successful"}