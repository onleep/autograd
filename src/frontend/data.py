import asyncio
from io import BytesIO

import pandas as pd
import streamlit as st

from clients.s3 import s3_download, s3close, s3init

SPEC_COLUMNS = {
    'base_power': 'power',
    'base_gear_type': 'gear_type',
    'general_auto_class': 'auto_class',
    'engine_max_power_kw': 'max_power_kw',
    'engine_displacement': 'displacement',
    'sizes_tires_rim_min': 'tires_rim_min',
    'sizes_width': 'width',
    'sizes_height': 'height',
    'sizes_disk_x1_min': 'disk_x1_min',
    'sizes_wheels_size_x0': 'wheels_size_x0',
    'volume_and_mass_full_weight': 'full_weight',
    'volume_and_mass_weight': 'weight',
}
TEXT_COLUMNS = ['mark', 'model', 'generation', 'trim', 'gear_type', 'auto_class']
MISSING = '__missing__'


@st.cache_data(show_spinner=False)
def download_data() -> bytes:
    async def fetch_data() -> bytes:
        await s3init()
        try:
            return await s3_download('data', 'train_df.parquet')
        finally:
            await s3close()

    return asyncio.run(fetch_data())


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    base_columns = ['mark', 'model', 'generation', 'trim', 'year', 'mileage', 'price']
    columns = [*base_columns, *SPEC_COLUMNS]
    data_raw = download_data()
    data = pd.read_parquet(BytesIO(data_raw), columns=columns)
    data = data.rename(columns=SPEC_COLUMNS).copy()
    numeric_columns = [column for column in data.columns if column not in TEXT_COLUMNS]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors='coerce')
    for column in TEXT_COLUMNS:
        values = data[column].astype('object')
        data[column] = values.map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    return data


def filter_data(df: pd.DataFrame, **filters: object) -> pd.DataFrame:
    data = df
    for column, value in filters.items():
        if value is None:
            continue
        if value == MISSING:
            data = data[data[column].isna()]
            continue
        data = data[data[column] == value]
    return data


def text_options(
    df: pd.DataFrame,
    column: str,
    *,
    include_missing: bool = False,
) -> list[str]:
    values = df[column].dropna().astype(str)
    options = sorted(value for value in values.unique().tolist() if value)
    if include_missing and df[column].isna().any():
        return [MISSING, *options]
    return options


def year_options(df: pd.DataFrame) -> list[int]:
    years = df['year'].dropna().astype(int).unique().tolist()
    return sorted(years, reverse=True)
