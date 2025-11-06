import re

from .types import ListInfo, PageInfo, TechInfo


def list_info(data: dict) -> ListInfo | None:
    if not (documents := data.get('documents', {})): return
    if not (vehicle_info := data.get('vehicle_info')): return
    if not (location := data.get('seller', {}).get('location')): return
    result: ListInfo = {
        'photos': {},
        'tags': data.get('tags'),
        'year': documents.get('year'),
        'owners': documents.get('owners_number'),
        'custom_cleared': documents.get('custom_cleared'),
        'predicted_prices': data.get('predicted_price_ranges'),
        'price': data.get('price_info', {}).get('price'),
        'mileage': data.get('state', {}).get('mileage'),
        'region': location.get('region_info', {}).get('name'),
        'mark': vehicle_info.get('mark_info', {}).get('code'),
        'model': vehicle_info.get('model_info', {}).get('code'),
    }
    for i in data.get('state', {}).get('image_urls', []):
        if not (pclass := i.get('photo_class', '').replace('AUTO_VIEW_', '')): continue
        if not i.get('sizes', {}).get('584x438'): continue
        result['photos'][pclass] = 'https:' + i['sizes']['584x438']
    strictValues = [
        'year', 'owners', 'mileage', 'price', 'custom_cleared', 'mark', 'model',
        'photos'
    ]
    if not all(result[k] for k in strictValues): return
    return result


def page_info(data: str) -> PageInfo:
    match = re.search(r'platform.*?},"description":"(.*?)"', data, re.DOTALL)
    descript = match.group(1).replace('\\n', ' ') if match and match.lastindex else None
    match = re.search(r'Цвет.*?<a[^>]*>(.*?)</a>', data, re.DOTALL)
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
