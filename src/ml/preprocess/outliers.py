import numpy as np
import pandas as pd


def clean_outliers(data: pd.DataFrame) -> pd.DataFrame:
    data = data[(data['year'] >= 2000) & (data['mileage'] < 1_000_000)]
    q = (
        data.groupby(['mark', 'model'], observed=True)['price']
        .quantile(np.array([0.01, 0.99]))
        .unstack()
        .rename(columns={0.01: 'low', 0.99: 'high'})
    )
    temp = data.join(q, on=['mark', 'model'])
    data = temp[
        ((temp['price'] >= temp['low']) & (temp['price'] <= temp['high']))
        | temp['low'].isna()
        | temp['high'].isna()
    ].drop(columns=['low', 'high'])
    q_low = data['price'].quantile(0.001)
    q_high = data['price'].quantile(0.999)
    data = data[(data['price'] >= q_low) & (data['price'] <= q_high)]
    subset = data.columns.difference(
        ['price', 'description', 'photos_name', 'predicted_prices']
    )
    return data.drop_duplicates(subset=subset)
