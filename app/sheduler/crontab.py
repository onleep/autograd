import asyncio

from aiocron import crontab
from parser.main import parse_cars
from parser.photo import parse_photos


async def cron() -> None:
    cronlist = [
        crontab('0 0 * * *', func=parse_cars),  # 24 hrs
        crontab('0 12 * * *', func=parse_photos),  # 12 hrs
    ]

    # yapf: disable # ruff: noqa
    try: await asyncio.Event().wait()
    except: [task.stop() for task in cronlist]
