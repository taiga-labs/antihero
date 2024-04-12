import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.web.app.events import SocketWrapper

fastapp = FastAPI()

origins = ["*"]
fastapp.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=["*"],
)

sockw = SocketWrapper()
sockw.setup()
socket_app = socketio.ASGIApp(socketio_server=sockw.sio)



