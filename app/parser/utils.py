import asyncio
import logging
from io import BytesIO
from time import time

from aiohttp import ClientError, ClientSession
from browserforge.fingerprints import FingerprintGenerator
from config import PROXIES
from PIL import Image

from .types import Fingerpring, ProxyData, Response

lock = asyncio.Lock()
template: ProxyData = {'session': None, 'cooldown': 0.0, 'errors': 0, 'lock': False}
proxies: dict[str, ProxyData] = {proxy: template.copy() for proxy in PROXIES}


async def request(
    url: str,
    session: ClientSession | None = None,
    params: dict | None = None,
    data: dict | None = None,
    json: dict | None = None,
    toJson: bool = False,
    status: int = 200,
    retry: int = 1,
    **kwargs,
) -> Response | None:
    proxy = jsond = raw = text = None
    for _ in range(retry):
        if not session:
            from .session import proxy_session
            proxy = await proxy_session()
            if not (session := proxy['session']): continue
        try:
            kwargs = {'json': json, 'allow_redirects': False, **kwargs}
            method = session.post if data or json else session.get
            async with method(url, params=params, data=data, **kwargs) as response:
                if response.status != status: raise ClientError('http_code')
                isImage = 'image' in response.headers['Content-Type']
                if toJson: jsond = await response.json(content_type=None)
                elif isImage: raw = await response.read()
                else: text = await response.text()
                error = jsond and (jsond.get('status') == 'ERROR' or jsond.get('error'))
                if error: raise ClientError('status')
                if proxy: proxy['errors'] = 0
                return {'data': response, 'json': jsond, 'text': text, 'raw': raw}
        except Exception as e:
            reqProxy = session._default_proxy
            logging.error(f'{reqProxy, url, type(e).__name__, str(e)}')
            if not proxy: continue
            session = None
            proxy['errors'] += 1
            proxy['cooldown'] = time() + 3 * 60
            if proxy['errors'] < 10: continue
            if proxy['session']: await proxy['session'].close()
            proxy['session'] = None
            proxy['errors'] = 0
        finally:
            if proxy:
                proxy['lock'] = False
                if proxy['cooldown'] < time():
                    proxy['cooldown'] = time() + 10


def gen_fp() -> Fingerpring:
    fp = FingerprintGenerator(device='desktop', locale='ru-RU').generate()
    screen = fp.screen
    layout = {
        'screen_height': screen.height,
        'screen_width': screen.width,
        'win_width': screen.outerWidth,
        'win_height': screen.outerHeight,
    }
    return {'headers': fp.headers, 'layout': layout}


async def get_proxy() -> str | None:
    async with lock:
        key_fn = lambda k: (proxies[k]['cooldown'])
        filtered = (i for i in proxies
                    if not proxies[i]['lock'] and proxies[i]['cooldown'] <= time() + 10)
        proxy = min(filtered, key=key_fn, default=None)
        if proxy: proxies[proxy]['lock'] = True
    return proxy


def to_jpeg(image: bytes):
    buffer = BytesIO()
    jpeg = Image.open(BytesIO(image))
    jpeg.convert('RGB').save(buffer, 'JPEG')
    return buffer.getvalue()


def lock_func():
    lock = asyncio.Lock()

    def decorator(func):

        async def wrapper(*args, **kwargs):
            if lock.locked(): return
            async with lock:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
