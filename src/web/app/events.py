from src.web import web_logger, socketio


@socketio.event
async def connect(sid, data):
    web_logger.info(f"connect | socket connection open | sid: {sid}")


@socketio.event
async def disconnect(sid):
    web_logger.info(f"disconnect | socket connection closed | sid: {sid}")


@socketio.event
async def set_connection(sid, data):
    web_logger.info(f"set_connection | socket set connection data | sid: {sid}")
