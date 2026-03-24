import pandas as pd

from clients.database import Offers


async def prepare_offers() -> pd.DataFrame:
    df_offers = pd.DataFrame(await Offers.all().values())
    drop_columns = ['id', 'autoru_hash', 'created_at', 'updated_at']
    df_offers.drop(columns=drop_columns, inplace=True)
    return df_offers
