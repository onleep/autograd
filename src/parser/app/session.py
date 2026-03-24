import asyncio
import logging
import re
from time import time

from aiohttp import ClientSession, ClientTimeout
from yarl import URL as yURL

from .types import ProxyData
from .utils import gen_fp, get_proxy, proxies, request

URL = 'https://auto.ru'
YDXURL = 'https://sso.passport.yandex.ru'


async def process(session: ClientSession) -> ClientSession:
    # get uuid
    fingerprint = gen_fp()
    session.cookie_jar.update_cookies({'autoru_gdpr': '1'})
    headers = {'Host': 'auto.ru', 'referer': f'{URL}/', 'priority': 'u=0, i'}
    session.headers.update(**fingerprint['headers'], **headers)
    first = await request(f'{URL}/', session, status=302) or {}
    X_Request_Id = first['data'].headers['X-Request-Id']
    uuid = yURL(first['data'].headers['Location']).query['uuid']
    # get container
    host = 'sso.passport.yandex.ru'
    headers = {'Host': host, 'referer': f'{URL}/', 'priority': 'u=0, i'}
    session.headers.update(headers)
    retpath = f'{URL}/?utm_referrer=https%3A%2F%2Fauto.ru%2F'
    params = {'retpath': retpath, 'uuid': uuid}
    second = await request(f'{YDXURL}/push', session, params)
    if not second or not (html := second['text']): raise Exception
    match = re.search(r"element2\.value\s*=\s*'([^']+)'", html)
    if not match or not (container := match.group(1)): raise Exception
    # get cookies
    params = {'uuid': uuid}
    data = {'retpath': retpath, 'container': container}
    headers = {
        'Host': 'sso.auto.ru',
        'Cache-Control': 'max-age=0',
        'Origin': f'{YDXURL}',
        'Referer': f'{YDXURL}/',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    session.headers.update(headers)
    third = await request('https://sso.auto.ru/install', session, params, data)
    if not third: raise Exception
    last = await request(f'{URL}/cars/kia/all/', session, headers={'Host': 'auto.ru'})
    if not last: raise Exception
    app_id = last['data'].headers['x-autoru-app-id'].split('=')[-1]
    # update cookies
    cookies = session.cookie_jar.filter_cookies(yURL(f'{URL}/'))
    headers = {
        'Host': 'auto.ru',
        'x-csrf-token': cookies['_csrf_token'].value,
        'x-page-request-id': X_Request_Id,
        'x-retpath-y': f'{URL}/cars/all/',
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/json',
        'x-client-app-version': app_id,
        'accept': '*/*',
        'origin': f'{URL}',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'same-origin',
        'sec-fetch-dest': 'empty',
        'referer': f'{URL}/cars/all/',
    }
    cookie_crashreport = {
        'route_name': 'card',
        'app_id': 'af-desktop-search',
        'time_spent': '1',
    }
    cookies = {
        'autoru_sso_redirect_blocked': '1',
        'sso_status': 'sso.passport.yandex.ru:synchronized_no_beacon',
        'yaPassportTryAutologin': '1',
        '_ym_isad': '2',
        'geo_onboarding_shown': 'true',
        'autoru_crashreport': cookie_crashreport,
        'autoru-visits-count': '1',
        'autoru-visits-session-unexpired': '1',
        'layout-config': fingerprint['layout'],
        'count-visits': '1',
        '_ym_d': cookies['from_lifetime'].value[:10],
    }
    session.headers.update(headers)
    session.cookie_jar.update_cookies(cookies)
    return session


async def proxy_session() -> ProxyData:
    if not (proxy := await get_proxy()):
        await asyncio.sleep(10)
        return await proxy_session()
    if (cooldown := proxies[proxy]['cooldown']) > time():
        await asyncio.sleep(cooldown - time())
    if proxies[proxy]['session']: return proxies[proxy]
    timeout = ClientTimeout(total=10)
    session = ClientSession(proxy=proxy, timeout=timeout)
    try:
        proxies[proxy]['session'] = await process(session)
        return proxies[proxy]
    except Exception as e:
        logging.error(f'{type(e).__name__, str(e) or "session"}')
        proxies[proxy]['cooldown'] = time() + 3 * 60
        proxies[proxy]['lock'] = False
        await session.close()
        return await proxy_session()


async def session_close():
    for proxy in proxies.values():
        if not proxy['session']: continue
        await proxy['session'].close()
