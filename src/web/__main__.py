from settings import settings
from src.web import app

app.run(debug=False, host="0.0.0.0", port=settings.MINIAPP_PORT)
