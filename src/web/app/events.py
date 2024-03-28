from src.web import web_logger, app


@app.sio.on("connect")
async def connect(sid, data):
    web_logger.info(f"connect | socket connection open | sid: {sid}")


@app.sio.on("disconnect")
async def disconnect(sid):
    web_logger.info(f"disconnect | socket connection closed | sid: {sid}")


@app.sio.on("set_connection")
async def set_connection(sid, data):
    web_logger.info(f"set_connection | socket set connection data | sid: {sid}")
