import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager

from src.web.app.routes import router

app = FastAPI()
socket_manager = SocketManager(app=app)

app.include_router(router=router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=["*"],
)

logging.basicConfig()
web_logger = logging.getLogger("ANTIHERO_WEB")
web_logger.setLevel(logging.INFO)
