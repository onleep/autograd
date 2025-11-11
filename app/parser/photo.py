import asyncio
import logging

from database.mysql import Photos
from s3.main import s3_upload
from tortoise.expressions import Q
from tortoise.functions import Count
from tortoise.queryset import QuerySet

from .utils import lock_func, request, to_jpeg


async def process_photo(photo: Photos, headers: dict):
    logging.info(f'Processing photo {photo.name} [{photo.id}]')
    resp = await request(photo.url, headers=headers, retry=5)
    if not resp or not (image := resp['raw']):
        return await Photos.filter(id=photo.id).update(status=photo.status - 1)
    imageType = resp['data'].headers['Content-Type'].split('/')[-1]
    if imageType != 'jpeg': image = await asyncio.to_thread(to_jpeg, image)
    await s3_upload(image, str(photo.autoru_id), f'{photo.name}.jpg')
    await Photos.filter(id=photo.id).update(status=1)
    logging.info(f'Processing photo {photo.name} [{photo.id}] completed')


def get_photos(target: dict) -> QuerySet[Photos]:
    return Photos.filter(
        name=target['name'],
        status__range=(-2, 0),
        autoru__mark=target['autoru__mark'],
        autoru__model=target['autoru__model'],
        autoru__year=target['autoru__year'],
    ).limit(50)


@lock_func()
async def parse_photos():
    headers = {'Host': 'photo.auto.ru'}
    targets = await Photos.annotate(count=Count('id', _filter=Q(status=1))) \
        .group_by('autoru__mark', 'autoru__model', 'autoru__year', 'name') \
        .filter(count__lt=50) \
        .values('autoru__mark', 'autoru__model', 'autoru__year', 'name')
    for i in range(0, len(targets), 100):
        batch = targets[i:i + 100]
        results = await asyncio.gather(*(get_photos(row) for row in batch))
        photos = [photo for result in results for photo in result]
        for j in range(0, len(photos), 100):
            batch2 = photos[j:j + 100]
            await asyncio.gather(*(process_photo(p, headers) for p in batch2))
            logging.info(f'Processed {j+len(batch2)} / {len(photos)} photos')
        logging.info(f'Processed {i+len(batch)} / {len(targets)} targets')
