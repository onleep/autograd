from io import BytesIO

from aioboto3 import Session
from config import S3_ID, S3_KEY


async def s3_download(folder: str, key: str) -> bytes:
    data = await s3.get_object(Bucket='main', Key=f'{folder}/{key}')
    return await data['Body'].read()


async def s3_upload(data: bytes, folder: str, key: str):
    await s3.upload_fileobj(BytesIO(data), 'main', f'{folder}/{key}')


async def s3init():
    global s3
    s3 = await Session().client(
        service_name='s3',
        aws_access_key_id=S3_ID,
        aws_secret_access_key=S3_KEY,
        endpoint_url='http://minio:9000',
    ).__aenter__()


async def s3close():
    global s3
    await s3.close()
