import logging

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from src.bot.factories import bot


app = Flask(__name__)
app.config["bot"] = bot

cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

socketio = SocketIO(app)

logging.basicConfig()
web_logger = logging.getLogger("ANTIHERO_WEB")
web_logger.setLevel(logging.INFO)
