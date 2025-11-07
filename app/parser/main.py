import asyncio
import logging
from datetime import datetime, timedelta
from time import time

from database.mysql import Attributes, Offers, Photos, Specifications
from s3.main import s3_upload

from .extractor import list_info, page_info, tech_info
from .types import ExtListInfo, TechInfo
from .utils import request

URL = 'https://auto.ru'
INFO_URL = f'{URL}/-/ajax/desktop-search'


async def insert(listInfo: ExtListInfo, techInfo: TechInfo, id: int):
    photos = listInfo['photos']
    offer_cols = Offers._meta.fields_map.keys()
    toOffers = {k: v for k, v in listInfo.items() if k in offer_cols}
    attr_cols = Attributes._meta.fields_map.keys()
    toAttrs = {k: v for k, v in listInfo.items() if k in attr_cols}
    toPhotos = [Photos(autoru_id=id, name=k, url=v) for k, v in photos.items()]
    try:
        await Offers.update_or_create(toOffers, autoru_id=id)
        await Specifications.update_or_create(dict(techInfo), autoru_id=id)
        await Attributes.update_or_create(toAttrs, autoru_id=id)
        await Photos.bulk_create(toPhotos, ignore_conflicts=True)
    except Exception as e:
        logging.error(f'{type(e).__name__, str(e)}')


async def collect(id: int, hash: str, paramId: int, offer: dict):
    # listInfo
    logging.info(f'Parsing car {id}-{hash}')
    if not (rawlistInfo := list_info(offer)): return
    # techInfo
    datenow = f'{time() * 1000:.0f}'
    url = f'{URL}/cars/used/{id}-{hash}/'
    headers = {'refer': url, 'x-retpath-y': url, 'x-client-date': datenow}
    jsonData = {'tech_param_id': paramId, 'geo_id': []}
    kwargs = {'headers': headers, 'json': jsonData}
    url = f'{INFO_URL}/getCatalogTechInfo/'
    techInfo = await request(url, toJson=True, retry=5, **kwargs)
    if not techInfo or not techInfo['json']: return
    if not (techInfo := tech_info(techInfo['json'])): return
    # description & color
    mark, model = rawlistInfo['mark'].lower(), rawlistInfo['model'].lower()
    url = f'{URL}/cars/used/sale/{mark}/{model}/{id}-{hash}/'
    pageInfo = await request(url, headers=headers, retry=5)
    pageInfo = pageInfo['text'] or '' if pageInfo else ''
    listInfo: ExtListInfo = {
        **rawlistInfo,
        **page_info(pageInfo),
        'autoru_hash': hash,
    }
    await insert(listInfo, techInfo, id)
    logging.info(f'Parsing car {id}-{hash} completed')


async def car_list(mark: str, sort: str):
    jsonData = {
        'with_discount': True,
        'catalog_filter': [{
            'mark': mark
        }],
        'section': 'used',
        'category': 'cars',
        'sort': sort,
        'output_type': 'list',
        'page': 1,
        'geo_id': [],
    }
    for pageNum in range(1, 99):
        logging.info(f'Parcing {mark} sort {sort} page {pageNum}')
        jsonData['page'] = pageNum
        url = f'{INFO_URL}/listing/'
        datenow = f'{time() * 1000:.0f}'
        hurl = f'{URL}/cars/{mark}/used/?sort={sort}&page={pageNum}'
        headers = {'refer': hurl, 'x-retpath-y': hurl, 'x-client-date': datenow}
        kwargs = {'headers': headers, 'json': jsonData}
        cars = await request(url, toJson=True, retry=5, **kwargs)
        if not cars or not (cars := cars['json']): continue
        if cars.get('pagination', {}).get('page') != pageNum: break
        tasks = []
        for offer in cars.get('offers', {}):
            id = offer.get('id')
            hash = offer.get('hash')
            vehicle_info = offer.get('vehicle_info', {})
            paramId = vehicle_info.get('tech_param', {}).get('id')
            if not all([id, hash, paramId]): continue
            offerdb = await Offers.get_or_none(autoru_id=id)
            if offerdb and offerdb.autoru_hash == hash: continue
            tasks.append(collect(id, hash, paramId, offer))
        await asyncio.gather(*tasks)
    logging.info(f'Parcing {mark} sort {sort} completed')


async def parse_cars():
    marks = [
        'KIA',
        'BMW',
        'TOYOTA',
        'HYUNDAI',
        'MERCEDES',
        'VOLKSWAGEN',
        'FORD',
    ]
    sorts = [
        'price_profitability-desc',
        'fresh_relevance_1-desc',
        'autoru_exclusive-desc',
        'cr_date-desc',
        'price-desc',
        'price-asc',
        'year-desc',
        'year-asc',
    ]
    [await car_list(mark, sort) for mark in marks for sort in sorts]


async def parse_photos():
    threeDays = datetime.now() - timedelta(days=3)
    photos = await Photos.filter(status=0, created_at__gte=threeDays)
    for photo in photos:
        logging.info(f'Processing photo {photo.name} id={photo.id}')
        image = await request(photo.url, retry=5)
        if not image or not image['raw']: continue
        await s3_upload(image['raw'], str(photo.autoru_id), f'{photo.name}.jpeg')
        await Photos.filter(id=photo.id).update(status=1)
