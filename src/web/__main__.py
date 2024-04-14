import uvicorn

from settings import settings
from src.web import fastapp, socket_app
from src.web.app.routes import router

fastapp.include_router(router=router)
fastapp.mount("/socket.io", socket_app)

uvicorn.run(
    app=fastapp,
    host="0.0.0.0",
    port=settings.MINIAPP_PORT,
    proxy_headers=True,
    forwarded_allow_ips="*",
)
