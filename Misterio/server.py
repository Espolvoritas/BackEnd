from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

# Standart html file to render on server startup
htmlfilepath = 'test.html'

@app.get("/")
async def get():
    return FileResponse(htmlfilepath)

