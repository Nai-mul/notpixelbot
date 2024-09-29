import os
import glob
import asyncio
import argparse
from itertools import cycle
from pyrogram import Client
from better_proxy import Proxy
from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions

start_text = """
███████╗██╗███████╗     ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
██╔════╝██║╚══███╔╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
███████╗██║  ███╔╝     ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
╚════██║██║ ███╔╝      ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
███████║██║███████╗    ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
╚══════╝╚═╝╚══════╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝

NotPixel BOT V 1.0
Prepared and Developed by: F.Davoodi

No session found. Please create a session first:
    1. Create a session 👨‍🎨
"""

def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [os.path.splitext(os.path.basename(file))[0] for file in session_names]
    return session_names

def get_proxies() -> list[Proxy]:
    proxies = []
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    return proxies

async def get_tg_clients() -> list[Client]:
    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("No session files found")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients

async def process() -> None:
    session_names = get_session_names()

    if session_names:
        logger.info(f"Found {len(session_names)} session(s), starting drawing...")
        tg_clients = await get_tg_clients()
        await run_tasks(tg_clients)
    else:
        print(start_text)
        logger.warning("No session found. Please create a session first.")
        await register_sessions()

async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(process())
    except Exception as e:
        logger.error(f"An error occurred: {e}")
