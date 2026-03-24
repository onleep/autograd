from io import BytesIO

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer

from clients.database import Attributes
from clients.s3 import s3_upload


async def to_mlb(column: pd.Series, name: str) -> pd.DataFrame:
    s = column.map(lambda x: x if isinstance(x, (list, np.ndarray)) else [])
    mlb = MultiLabelBinarizer(sparse_output=False)
    X_target = np.asarray(mlb.fit_transform(s))
    buffer = BytesIO()
    joblib.dump(mlb, buffer)
    await s3_upload(buffer, 'data', f'mlb_{name}.pkl')
    return pd.DataFrame(
        X_target,
        index=column.index,
        columns=[f'{name}_{c}' for c in mlb.classes_],
    )


async def prepare_attrs() -> pd.DataFrame:
    df_attrs = pd.DataFrame(await Attributes.all().values())
    drop_columns = ['id', 'created_at', 'updated_at']
    df_attrs.drop(columns=drop_columns, inplace=True)
    # equip
    df_equip = await to_mlb(df_attrs['equipment'], 'equip')
    df_attrs = df_attrs.join(df_equip)
    df_attrs.drop(columns=['equipment'], inplace=True)
    # tags
    df_tags = await to_mlb(df_attrs['tags'], 'tags')
    df_attrs = df_attrs.join(df_tags)
    df_attrs.drop(columns=['tags'], inplace=True)
    # filter by year
    df_attrs = df_attrs[df_attrs['published_at'] >= '2025-01-01'].copy()
    df_attrs['pub_year'] = df_attrs['published_at'].dt.year  # type: ignore
    df_attrs['pub_month'] = df_attrs['published_at'].dt.month  # type: ignore
    df_attrs.drop(columns=['published_at'], inplace=True)
    # vin
    vin_df = df_attrs['vin'].apply(pd.Series)
    vin_df.drop(columns=['pts_owners'], inplace=True)
    vin_df = vin_df.add_prefix('vin_')
    df_attrs = df_attrs.join(vin_df)
    df_attrs.drop(columns=['vin'], inplace=True)
    df_attrs.apply(
        lambda s: s.nunique() if s.dtype != 'object' else s.astype(str).nunique()
    )
    df_attrs.dropna(subset=['is_dealer', 'color'], inplace=True)
    df_attrs.drop(columns=['custom_cleared', 'user_id'], inplace=True)
    return df_attrs
