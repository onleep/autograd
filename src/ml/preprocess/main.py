import logging
import tempfile

import pandas as pd

from clients.s3 import s3_upload
from config import FEATURES

from .aggs import build_aggregates
from .attrs import prepare_attrs
from .offers import prepare_offers
from .outliers import clean_outliers
from .photos import prepare_photos
from .specs import prepare_specs


async def upload_df(data: pd.DataFrame, name: str):
    with tempfile.NamedTemporaryFile() as file:
        data.to_parquet(file.name, index=False)
        await s3_upload(file.read(), 'data', f'{name}.parquet')


async def preprocess():
    logging.info('Start prepare_offers')
    data = await prepare_offers()
    logging.info('Start prepare_specs')
    data = data.merge(await prepare_specs(), on='autoru_id', how='inner')
    logging.info('Start prepare_attrs')
    data = data.merge(await prepare_attrs(), on='autoru_id', how='inner')
    logging.info('Start prepare_photos')
    data = data.merge(await prepare_photos(), on='autoru_id', how='inner')
    data = clean_outliers(data)
    obj_cols = data.select_dtypes(include='object').columns.difference(
        ['predicted_prices', 'photos_name']
    )
    data[obj_cols] = data[obj_cols].fillna('').astype(str)
    if FEATURES: data = data[FEATURES]  # fmt: off
    await upload_df(data, 'train_df')
    logging.info('Aggregate train_df')
    await upload_df(build_aggregates(data), 'aggs_df')
