import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pydantic import BaseModel
import dataclasses
import requests
import uvicorn

from src.racing.routes import router as racing_api_router
from src.user.routes import router as user_api_router

_FE_DIR = os.path.join(os.getcwd(), 'frontend')

app = FastAPI()

app.include_router(racing_api_router)
app.include_router(user_api_router)
app.mount('/static', StaticFiles(directory=_FE_DIR), name='static')

@app.get("{path:path}")
async def index(path):
    return FileResponse(os.path.join(_FE_DIR, 'index.html'))


if __name__ == '__main__':
  uvicorn.run('src.main:app', host='0.0.0.0', reload=True, port=8000)

