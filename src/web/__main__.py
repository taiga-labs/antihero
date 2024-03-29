import uvicorn

from settings import settings
from src.web import fastapp
from src.web.app.routes import router

fastapp.include_router(router=router)

uvicorn.run(
    app=fastapp,
    host="0.0.0.0",
    port=settings.MINIAPP_PORT,
    proxy_headers=True,
    forwarded_allow_ips="*",
)
