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


async def load_model():
    model_raw, mlb_tags_raw, mlb_quip_raw = await asyncio.gather(
        s3_download('data', API_MODEL),
        s3_download('data', 'mlb_tags.pkl'),
        s3_download('data', 'mlb_equip.pkl'),
    )
    with tempfile.NamedTemporaryFile() as file:
        file.write(model_raw)
        model = CatBoostRegressor()
        model.load_model(file.name)
    mlb_tags: MultiLabelBinarizer = joblib.load(BytesIO(mlb_tags_raw))
    mlb_quip: MultiLabelBinarizer = joblib.load(BytesIO(mlb_quip_raw))
    return model, mlb_tags, mlb_quip


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


def prepredict(request: dict, state: AppState):
    data_dict = request['offer']
    data_dict.update(request['attributes'] or {})
    data_dict.update(flatten_specs(request['specifications'] or {}))
    data = pd.DataFrame([data_dict])
    if 'equipment' in data:
        df_equip = mlb_encode(state.mlb_quip, data['equipment'], 'equip')
        data = data.drop(columns=['equipment'])
        data = data.join(df_equip)
    if 'tags' in data:
        df_tags = mlb_encode(state.mlb_tags, data['tags'], 'tags')
        data = data.drop(columns=['tags'])
        data = data.join(df_tags)
    assert state.model.feature_names_ is not None
    cat_idx = state.model.get_cat_feature_indices()
    data = data.reindex(columns=state.model.feature_names_)
    cat_cols = [state.model.feature_names_[i] for i in cat_idx]
    data[cat_cols] = data[cat_cols].fillna('').astype(str)
    return data
