import pandas as pd

from clients.database import Photos


async def prepare_photos() -> pd.DataFrame:
    df_photos = pd.DataFrame(await Photos.all().values())
    drop_columns = ['id', 'url', 'created_at', 'updated_at']
    df_photos.drop(columns=drop_columns, inplace=True)
    df_photos = df_photos[df_photos['status'] == 1]
    df_photos = df_photos.groupby('autoru_id')['name'].agg(list).reset_index()
    df_photos.rename(columns={'name': 'photos_name'}, inplace=True)
    return df_photos
