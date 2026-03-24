import logging
import tempfile
from datetime import date
from io import BytesIO

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split

from clients.s3 import s3_download, s3_upload
from config import TRAIN_MODE

from .embedding import embedding
from .outliers import clean_outliers


async def load_data() -> pd.DataFrame:
    data = await s3_download('data', 'train_df.parquet')
    data = pd.read_parquet(BytesIO(data))
    obj_cols = data.select_dtypes(include='object').columns.difference(
        ['predicted_prices', 'photos_name']
    )
    data[obj_cols] = data[obj_cols].fillna('').astype(str)
    return data


def get_pools(data: pd.DataFrame, columns: list) -> tuple[Pool, Pool, Pool]:
    x_train, x_temp, y_train, y_temp = train_test_split(
        data.drop(columns=columns),
        np.log1p(data['price']),
        test_size=0.3,
        random_state=42,
        stratify=data['mark'],
    )
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=0.5,
        random_state=42,
        stratify=x_temp['mark'],
    )
    cat_features = x_train.select_dtypes(include='object').columns.to_list()
    train_pool = Pool(x_train, label=y_train, cat_features=cat_features)
    test_pool = Pool(x_test, label=y_test, cat_features=cat_features)
    val_pool = Pool(x_val, label=y_val, cat_features=cat_features)
    return train_pool, test_pool, val_pool


def eval_metrics(model: CatBoostRegressor, val_pool: Pool) -> dict[str, float]:
    pred = np.expm1(model.predict(val_pool))
    true = np.expm1(val_pool.get_label())
    return {
        'R2': r2_score(true, pred),
        'MAE': mean_absolute_error(true, pred),
        'RMSE': root_mean_squared_error(true, pred),
        'MAPE': mean_absolute_percentage_error(true, pred),
    }


async def upload_model(model: CatBoostRegressor) -> None:
    with tempfile.NamedTemporaryFile() as file:
        model.save_model(file.name)
        name = f'model_{date.today()}.cbm'
        await s3_upload(open(file.name, 'rb'), 'data', name)


async def train() -> None:
    logging.info('Clean outliers')
    data = clean_outliers(await load_data())
    columns = ['price', 'photos_name', 'predicted_prices', 'description']
    if TRAIN_MODE == '1':
        logging.info('Embedding')
        data = embedding(data)
        columns.remove('description')
    train_pool, test_pool, val_pool = get_pools(data, columns)
    model = CatBoostRegressor(random_seed=42)
    logging.info('Fit model')
    model.fit(train_pool, eval_set=val_pool)
    logging.info('Upload model')
    await upload_model(model)
    logging.info({'metrics': eval_metrics(model, test_pool)})
