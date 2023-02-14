import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import dataclasses
import requests
import uvicorn

from racing.routes import router as racing_api_router

_FE_DIR = os.path.join(os.getcwd(), 'frontend')

app = FastAPI()
app.include_router(racing_api_router)
app.mount('/static', StaticFiles(directory=_FE_DIR), name='static')
app.mount('/', StaticFiles(directory=_FE_DIR, html=True), name='index')


if __name__ == '__main__':
  uvicorn.run("main:app", host='0.0.0.0', reload=True, port=8000)

