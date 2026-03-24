import asyncio
import logging

from clients.database import Offers, dbclose, dbinit
from clients.s3 import s3close, s3init
from config import ML_MODE

from .preprocess.main import preprocess
from .train.main import train


async def main() -> None:
    if ML_MODE == '0':
        return logging.info('TRAIN_MODEL = 0')
    await asyncio.gather(dbinit(), s3init())
    if await Offers.all().count() > 100_000:
        if ML_MODE in ('1', '2'):
            await preprocess()
        if ML_MODE in ('2', '3'):
            await train()
    else:
        logging.error('Insufficient data')
    await asyncio.gather(dbclose(), s3close())


if __name__ == '__main__':
    asyncio.run(main())
