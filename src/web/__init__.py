import logging

from flask import Flask, Response
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO

from src.bot.factories import bot


app = Flask(__name__)
app.config["bot"] = bot

# cors = CORS(app, resources={r"*": {"origins": "*"}})
# cors = CORS(app, resources={r"/*": {"origins": "*"}})
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.route("/", methods=["OPTIONS", "GET"])
# @cross_origin()
def start():
    response = Response(status=200)
    return response


# @app.after_request
# def after_request(response):
#     response.headers.add("Access-Control-Allow-Origin", "*")
#     response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
#     response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE")
#    return response


# socketio = SocketIO(app)

logging.basicConfig()
web_logger = logging.getLogger("ANTIHERO_WEB")
web_logger.setLevel(logging.INFO)
