from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pony.orm.core import select
from games import game

app = FastAPI()

# Standart html file to render on server startup
htmlfilepath = 'test.html'

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game)

@app.get("/")
async def get():
    return FileResponse(htmlfilepath)