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
from config import TRAIN_MODE, TRAIN_TARGET


async def load_data() -> pd.DataFrame:
    data = await s3_download('data', 'train_df.parquet')
    return pd.read_parquet(BytesIO(data))


def get_target(row: pd.Series) -> float:
    if TRAIN_TARGET == 'predicted_prices':
        target = row[TRAIN_TARGET]
        for key in ('autoru', 'tag_range', 'q5050', 'q4060'):
            if target.get(key) and target[key].get('from') and target[key].get('to'):
                return float(np.mean([target[key]['from'], target[key]['to']]))
    return row['price']


def get_pools(data: pd.DataFrame, columns: list) -> tuple[Pool, Pool, Pool]:
    x_train, x_temp, y_train, y_temp = train_test_split(
        data.drop(columns=columns),
        np.log1p(data.apply(get_target, axis=1)),
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
    params = {'cat_features': cat_features}
    if TRAIN_MODE == '1': params['text_features'] = ['description']  # fmt: off
    train_pool = Pool(x_train, label=y_train, **params)
    test_pool = Pool(x_test, label=y_test, **params)
    val_pool = Pool(x_val, label=y_val, **params)
    return train_pool, test_pool, val_pool


def eval_metrics(model: CatBoostRegressor, test_pool: Pool) -> dict[str, float]:
    pred = np.expm1(model.predict(test_pool))
    true = np.expm1(test_pool.get_label())
    return {
        'R2': r2_score(true, pred),
        'MAE': mean_absolute_error(true, pred),
        'RMSE': root_mean_squared_error(true, pred),
        'MAPE': mean_absolute_percentage_error(true, pred),
    }


async def upload_model(model: CatBoostRegressor, metric: float) -> None:
    with tempfile.NamedTemporaryFile() as file:
        model.save_model(file.name)
        name = f'model_{date.today()}_{metric:.4f}.cbm'
        await s3_upload(file.read(), 'data', name)


async def train() -> None:
    logging.info('Load data')
    data = await load_data()
    columns = ['price', 'photos_name', 'predicted_prices', 'autoru_id', 'description']
    if TRAIN_MODE in ('1', '2'):
        columns.remove('description')
        if TRAIN_MODE == '2':
            from .embedding import embedding

            logging.info('Embedding')
            data = embedding(data)
    train_pool, test_pool, val_pool = get_pools(data, columns)
    model = CatBoostRegressor(random_seed=42, iterations=5000)
    logging.info('Fit model')
    model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=100)
    logging.info('Upload model')
    metrics = eval_metrics(model, test_pool)
    await upload_model(model, metrics['R2'])
    logging.info({'metrics': metrics})
