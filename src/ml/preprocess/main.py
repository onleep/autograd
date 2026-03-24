import logging
import tempfile

import pandas as pd

from clients.s3 import s3_upload

from .attrs import prepare_attrs
from .offers import prepare_offers
from .photos import prepare_photos
from .specs import prepare_specs


async def upload_df(data: pd.DataFrame, name: str):
    with tempfile.NamedTemporaryFile() as file:
        data.to_parquet(file.name, index=False)
        await s3_upload(open(file.name, 'rb'), 'data', f'{name}.parquet')


async def preprocess():
    logging.info('Start prepare_offers')
    data = await prepare_offers()
    logging.info('Start prepare_specs')
    data = data.merge(await prepare_specs(), on='autoru_id', how='inner')
    logging.info('Start prepare_attrs')
    data = data.merge(await prepare_attrs(), on='autoru_id', how='inner')
    logging.info('Start prepare_photos')
    data = data.merge(await prepare_photos(), on='autoru_id', how='inner')
    data.drop(columns=['autoru_id'], inplace=True)
    await upload_df(data, 'train_df')
