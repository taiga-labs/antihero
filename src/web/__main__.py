import uvicorn

from settings import settings
from src.web import fastapp, socket_app
from src.web.app.routes import router
from src.web.app.utils import add_exception_handler

fastapp.include_router(router=router)
add_exception_handler(fastapp)
fastapp.mount("/socket.io", socket_app)

uvicorn.run(
    app=fastapp,
    host="0.0.0.0",
    port=settings.MINIAPP_PORT,
    proxy_headers=True,
    forwarded_allow_ips="*",
)
