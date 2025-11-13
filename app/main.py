from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.router_page import router as router_page
from api.router_socket import router as router_socket
import uvicorn
import asyncio
import threading
from core.tunnel_launcher import run_tunnel
from core.bot_launcher import run_bot

app = FastAPI()
app.mount('/static', StaticFiles(directory='app/static'), name='static')
app.include_router(router_socket)
app.include_router(router_page)

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    # Запуск туннеля
    run_tunnel()

    # Запуск FastAPI в отдельном потоке
    threading.Thread(target=run_server, daemon=True).start()

    # Небольшая задержка, чтобы туннель успел выдать URL и обновить .env
    await asyncio.sleep(5)

    # Запуск Telegram-бота
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())
