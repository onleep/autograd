import asyncio
import logging
from time import time

from database.mysql import Attributes, Offers, Photos, Specifications

from .extractor import list_info, page_info, tech_info
from .types import ExtListInfo, TechInfo
from .utils import lock_func, request

URL = 'https://auto.ru'
INFO_URL = f'{URL}/-/ajax/desktop-search'


async def insert(listInfo: ExtListInfo, techInfo: TechInfo, id: int):
    photos = listInfo['photos']
    toInsert = {k: v for k, v in listInfo.items() if v is not None}
    offer_cols = Offers._meta.fields_map.keys()
    toOffers = {k: v for k, v in toInsert.items() if k in offer_cols}
    attr_cols = Attributes._meta.fields_map.keys()
    toAttrs = {k: v for k, v in toInsert.items() if k in attr_cols}
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
    if not (listInfo := list_info(offer)): return
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
    # vinReport
    jsonData = {
        'offerID': f'{id}-{hash}',
        'category': 'cars',
        'isCardPage': True,
        'geo_id': [],
    }
    url = f'{INFO_URL}/getRichVinReport/'
    kwargs = {'headers': headers, 'json': jsonData}
    vinReport = await request(url, toJson=True, retry=5, **kwargs)
    vinReport = i if vinReport and (i := vinReport['json']) else {}
    pts_owners = vinReport.get('report', {}).get('pts_owners', {})
    owners_count = pts_owners.get('owners_count_report') or 0
    listInfo['owners'] = max(listInfo['owners'], owners_count)
    # description & color
    mark, model = listInfo['mark'].lower(), listInfo['model'].lower()
    url = f'{URL}/cars/used/sale/{mark}/{model}/{id}-{hash}/'
    pageInfo = await request(url, headers=headers, retry=5)
    pageInfo = i if pageInfo and (i := pageInfo['text']) else ''
    extListInfo: ExtListInfo = {
        **listInfo,
        **page_info(pageInfo),
        'autoru_hash': hash,
    }
    await insert(extListInfo, techInfo, id)
    logging.info(f'Parsing car {id}-{hash} completed')


async def car_list(mark: str, model: str, sort: str) -> bool:
    jsonData = {
        'with_discount': True,
        'resolution_filter': [
            'is_pts_ok',
            'is_legal_ok',
            'is_accidents_ok',
        ],
        'catalog_filter': [{
            'mark': mark,
            'model': model
        }],
        'section': 'used',
        'category': 'cars',
        'search_tag': ['real_photo', ],
        'sort': sort,
        'output_type': 'list',
        'page': 1,
        'geo_id': [],
    }
    for pageNum in range(1, 100):
        logging.info(f'Parcing {mark}:{model} sort {sort} page {pageNum}')
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
    logging.info(f'Parcing {mark}:{model} sort {sort} completed')
    return True if jsonData['page'] == 99 else False


@lock_func()
async def parse_cars():
    marks = [
        'KIA',
        'BMW',
        'FORD',
        'TOYOTA',
        'NISSAN',
        'HYUNDAI',
        'MERCEDES',
        'VOLKSWAGEN',
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
    rows = await Photos.filter(mark__in=marks).group_by(
        'autoru__mark',
        'autoru__model',
    ).values('autoru__mark', 'autoru__model')
    mark_models = {mark: set(['']) for mark in marks}
    [mark_models[r['autoru__mark']].add(r['autoru__model']) for r in rows]
    for mark, models in mark_models.items():
        for model in models:
            for sort in sorts:
                if not await car_list(mark, model, sort): break
