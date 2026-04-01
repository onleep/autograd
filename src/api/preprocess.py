import asyncio
import tempfile
from io import BytesIO

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.preprocessing import MultiLabelBinarizer

from clients.s3 import s3_download
from config import API_MODEL

from .models import AppState


async def load_artifacts():
    model_raw, mlb_tags_raw, mlb_quip_raw, train_df_raw = await asyncio.gather(
        s3_download('data', API_MODEL),
        s3_download('data', 'mlb_tags.pkl'),
        s3_download('data', 'mlb_equip.pkl'),
        s3_download('data', 'train_df.parquet'),
    )
    with tempfile.NamedTemporaryFile() as file:
        file.write(model_raw)
        model = CatBoostRegressor()
        model.load_model(file.name)
    train_df: pd.DataFrame = pd.read_parquet(BytesIO(train_df_raw))
    train_df = train_df.drop(columns=['price', 'photos_name', 'predicted_prices'])
    mlb_tags: MultiLabelBinarizer = joblib.load(BytesIO(mlb_tags_raw))
    mlb_quip: MultiLabelBinarizer = joblib.load(BytesIO(mlb_quip_raw))
    return model, mlb_tags, mlb_quip, train_df


def mlb_encode(mlb: MultiLabelBinarizer, column: pd.Series, name: str) -> pd.DataFrame:
    s = column.map(lambda x: x if isinstance(x, (list, np.ndarray)) else [])
    s = s.map(lambda x: [v for v in x if v in mlb.classes_])
    return pd.DataFrame(
        np.asarray(mlb.transform(s)),
        index=column.index,
        columns=[f'{name}_{c}' for c in mlb.classes_],
    )


def flatten_specs(values: dict) -> dict:
    flat: dict = {}
    for section, payload in values.items():
        if not isinstance(payload, dict):
            flat[section] = payload
            continue
        for key, value in payload.items():
            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    flat[f'{section}_{key}_{inner_key}'] = inner_value
                continue
            flat[f'{section}_{key}'] = value
    return flat


def get_subset(data: pd.Series, train_df: pd.DataFrame) -> pd.DataFrame:
    importants = ['mark', 'model', 'year', 'generation', 'trim']
    cols = [c for c in importants if c in data and pd.notna(data[c])]
    return train_df[(train_df[cols] == data[cols]).all(1)]


def fill_data(data: pd.Series, subset: pd.DataFrame, cat_cols: list) -> pd.Series:
    data = data[data.index.intersection(subset.columns)]
    subset[cat_cols] = subset[cat_cols].fillna('').astype(str)
    for col in subset.columns:
        if col in data and pd.notna(data[col]):
            continue
        elif col not in cat_cols:
            data[col] = subset[col].mean()
        else:
            data[col] = subset[col].mode().iloc[0]
    return data


def prepredict(request: dict, state: AppState) -> pd.Series:
    data_dict = request['offer']
    data_dict.update(request['attributes'] or {})
    data_dict.update(flatten_specs(request['specifications'] or {}))
    data = pd.Series(data_dict)
    if data['equipment'] is not None:
        data = data.join(mlb_encode(state.mlb_quip, data['equipment'], 'equip'))
    if data['tags'] is not None:
        data = data.join(mlb_encode(state.mlb_tags, data['tags'], 'tags'))
    subset = get_subset(data, state.train_df)
    assert state.model.feature_names_ is not None
    cat_idx = state.model.get_cat_feature_indices()
    cat_cols = [state.model.feature_names_[i] for i in cat_idx]
    data = fill_data(data, subset, cat_cols)
    return data.reindex(state.model.feature_names_)
