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

from .embedding import embedding
from .models import AppState
from .photo_features import photo_features


async def load_artifacts():
    model_raw, mlb_tags_raw, mlb_quip_raw, aggs_df_raw = await asyncio.gather(
        s3_download('data', API_MODEL),
        s3_download('data', 'mlb_tags.pkl'),
        s3_download('data', 'mlb_equip.pkl'),
        s3_download('data', 'aggs_df.parquet'),
    )
    with tempfile.NamedTemporaryFile() as file:
        file.write(model_raw)
        model = CatBoostRegressor()
        model.load_model(file.name)
    aggs_df: pd.DataFrame = pd.read_parquet(BytesIO(aggs_df_raw))
    mlb_tags: MultiLabelBinarizer = joblib.load(BytesIO(mlb_tags_raw))
    mlb_quip: MultiLabelBinarizer = joblib.load(BytesIO(mlb_quip_raw))
    return model, mlb_tags, mlb_quip, aggs_df


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


def fill_data(data: pd.Series, aggs_df: pd.DataFrame) -> pd.Series:
    all_keys = ['mark', 'model', 'year', 'generation', 'trim']
    keys = [key for key in all_keys if pd.notna(data[key])]
    subset = aggs_df[aggs_df['group'] == str(keys)]
    row = subset[(subset[keys] == data[keys]).all(1)].iloc[0]
    for col in row.index:
        if col == 'group': continue  # fmt: off
        if col in data and pd.notna(data[col]): continue  # fmt: off
        data[col] = row[col]
    return data


async def prepredict(request: dict, state: AppState) -> pd.Series:
    data_dict = request['offer']
    data_dict.update(request['photos'])
    data_dict.update(request['attributes'])
    data_dict.update(flatten_specs(request['specifications']))
    data = pd.Series(data_dict)
    if data['equipment'] is not None:
        data = data.join(mlb_encode(state.mlb_quip, data['equipment'], 'equip'))
    if data['tags'] is not None:
        data = data.join(mlb_encode(state.mlb_tags, data['tags'], 'tags'))
    if data['photos'] is not None:
        data = await photo_features(data)
    if data['description'] is not None:
        data = embedding(data)
    data = fill_data(data, state.aggs_df)
    return data.reindex(state.model.feature_names_)
