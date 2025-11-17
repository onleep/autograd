import re
from datetime import datetime

from .types import ListInfo, PageInfo, TechInfo


def list_info(data: dict) -> ListInfo | None:
    if not (documents := data.get('documents', {})): return
    if not (vehicle_info := data.get('vehicle_info')): return
    if not (extra := data.get('additional_info', {})): return
    if not (location := data.get('seller', {}).get('location')): return
    if (published_at := extra.get('creation_date')) and published_at.isdigit():
        published_at = datetime.fromtimestamp(int(published_at) / 1000)
    equipment = [k for k, v in vehicle_info.get('equipment', {}).items() if v]
    user_ref = data.get('user_ref', '').split(':')
    result: ListInfo = {
        'photos': {},
        'tags': data.get('tags'),
        'published_at': published_at,
        'equipment': equipment or None,
        'user_id': user_ref[-1] or None,
        'year': documents.get('year'),
        'owners': documents.get('owners_number'),
        'custom_cleared': documents.get('custom_cleared'),
        'price': data.get('price_info', {}).get('price'),
        'mileage': data.get('state', {}).get('mileage'),
        'predicted_prices': data.get('predicted_price_ranges'),
        'region': location.get('region_info', {}).get('name'),
        'mark': vehicle_info.get('mark_info', {}).get('code'),
        'model': vehicle_info.get('model_info', {}).get('code'),
        'trim': vehicle_info.get('complectation', {}).get('name'),
        'generation': vehicle_info.get('super_gen', {}).get('name'),
        'is_dealer': dict(dealer=True, user=False).get(user_ref[0]),
    }
    for i in data.get('state', {}).get('image_urls', []):
        if not (pclass := i.get('photo_class', '').replace('AUTO_VIEW_', '')): continue
        if not i.get('sizes', {}).get('584x438'): continue
        if pclass in ('BACK_LEFT', 'BACK_RIGHT'): pclass = 'BACK'
        elif pclass in ('FRONT_LEFT', 'FRONT_RIGHT'): pclass = 'FRONT'
        pclass = pclass.replace('3_4_', '')
        whitelist = [
            'BACK', 'FRONT', 'SIDE_LEFT', 'SIDE_RIGHT', 'BACK_LEFT', 'BACK_RIGHT',
            'FRONT_LEFT', 'FRONT_RIGHT'
        ]
        if pclass not in whitelist: continue
        result['photos'][pclass] = 'https:' + i['sizes']['584x438']
    strict = [
        'owners', 'mileage', 'price', 'custom_cleared', 'mark', 'model', 'published_at'
    ]
    if any(result[k] is None for k in strict + ['year']) or not result['photos']: return
    return result


def page_info(data: str) -> PageInfo:
    match = re.search(r'platform.*?},"description"\s*:\s*"((?:[^"\\]|\\.)*)"', data)
    descript = match.group(1) if match and match.lastindex else None
    if descript: descript = re.sub(r'(\\[ntr])|\s+', ' ', descript)
    match = re.search(r'Цвет\s*</div>\s*<a[^>]*>(.*?)</a>', data)
    color = match.group(1).capitalize() if match and match.lastindex else None
    return {'description': descript, 'color': color}


def tech_info(data: dict) -> TechInfo | None:
    data = data.get('data', {})
    result: TechInfo = {
        'performance_indicators': None,
        'volume_and_mass': None,
        'transmission': None,
        'engine': None,
        'base': None,
        'sizes': None,
        'general': None,
        'suspension_and_brakes': None,
    }
    tech_info = data.get('tech_info_group', [])
    for info in tech_info:
        if info.get('id', '') == 'NO_GROUP': info['id'] = 'base'
        if (id := info['id'].lower()) not in result: continue
        [i.pop('name', '') for i in info.get('entity', {})]
        result[id] = {item.pop('id', ''): item for item in info.get('entity', {})}
    engine_id = data.get('common_tech_info', {}).get('engine_id', [])
    body_type = data.get('common_tech_info', {}).get('body_type')
    engine_id = engine_id[0] if len(engine_id) else None
    if result['engine'] and engine_id:
        result['engine']['engine_id'] = {'value': engine_id}
    if result['base'] and body_type:
        result['base']['body_type'] = {'value': body_type}
    if not any(result.values()): return
    return result
