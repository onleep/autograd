import asyncio

from clients.s3 import s3close, s3init

from .fastapi import fastapi


async def main() -> None:
    await s3init()
    await fastapi()
    await s3close()


if __name__ == '__main__':
    asyncio.run(main())
