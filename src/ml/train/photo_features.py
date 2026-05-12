import asyncio
import base64
import json
import logging
from typing import Any

import pandas as pd
from aiohttp import ClientSession

from clients.s3 import s3_download
from config import VLM_MODEL, VLM_URL

from .photo_config import PROMPT, QUESTIONS, RESPONSE_FORMAT


async def get_images(autoru_id: str, photos_name: list[str]) -> list[dict[str, Any]]:
    content = []
    for photo_name in photos_name:
        raw_photo = await s3_download(autoru_id, f'{photo_name}.jpg')
        encoded = base64.b64encode(raw_photo).decode()
        photo = f'data:image/jpeg;base64,{encoded}'
        content.append({'type': 'image_url', 'image_url': {'url': photo}})
    return content


def build_payload(images: list[dict[str, Any]]) -> dict[str, Any]:
    message = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': PROMPT},
                *images,
            ],
        }
    ]
    return {
        'model': VLM_MODEL,
        'messages': message,
        'temperature': 0,
        'max_tokens': 256,
        'response_format': RESPONSE_FORMAT,
    }


async def request_vlm(
    session: ClientSession, payload: dict[str, Any]
) -> dict[str, Any] | None:
    for attemp in range(3):
        try:
            async with session.post(VLM_URL, json=payload) as response:
                response.raise_for_status()
                response = await response.json()
                content = response['choices'][0]['message']['content']
                return json.loads(content)
        except Exception:
            logging.exception('VLM request failed')
            if attemp < 3: await asyncio.sleep(2)  # fmt: off


async def process_row(session: ClientSession, index: Any, row: pd.Series):
    images = await get_images(row['autoru_id'], row['photos_name'])
    payload = build_payload(images)
    features = await request_vlm(session, payload)
    return index, features


async def photo_features(data: pd.DataFrame, batch_size: int = 16):
    async with ClientSession() as session:
        for start in range(0, len(data), batch_size):
            batch = data.iloc[start : start + batch_size]
            tasks = [
                process_row(session, index, row) for index, row in batch.iterrows()
            ]
            results = await asyncio.gather(*tasks)
            for index, features in results:
                logging.info(f'features: {features}')
                if features is None: continue  # fmt: off
                data.loc[index, list(QUESTIONS.keys())] = list(features.values())
            if (start + len(batch)) % 10000 < batch_size:
                logging.info(f'Processed {start + len(batch)} / {len(data)} rows')

    return data
