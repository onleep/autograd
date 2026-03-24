import asyncio

from clients.database import dbclose, dbinit
from clients.s3 import s3close, s3init

from .app.session import session_close
from .sheduler.crontab import cron


async def main() -> None:
    await asyncio.gather(dbinit(), s3init())
    await cron()  # app
    await session_close()
    await asyncio.gather(dbclose(), s3close())


if __name__ == '__main__':
    asyncio.run(main())
