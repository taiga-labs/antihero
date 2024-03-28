import uvicorn

from settings import settings
from src.web import app

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=settings.MINIAPP_PORT,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
