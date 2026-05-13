import json
import logging
from typing import Any

import pandas as pd
from aiohttp import ClientSession, ClientTimeout

from config import VLM_MODEL, VLM_URL

from .photo_config import PROMPT, QUESTIONS, RESPONSE_FORMAT


def build_content(images: list[str]) -> list[dict[str, Any]]:
    content = []
    for image in images:
        photo = f'data:image/jpeg;base64,{image}'
        content.append({'type': 'image_url', 'image_url': {'url': photo}})
    return [{'type': 'text', 'text': PROMPT}, *content]


def build_payload(content: list[dict[str, Any]]) -> dict[str, Any]:
    message = [{'role': 'user', 'content': content}]
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
    try:
        async with session.post(VLM_URL, json=payload) as response:
            response.raise_for_status()
            response = await response.json()
            content = response['choices'][0]['message']['content']
            return json.loads(content)
    except Exception:
        logging.exception('VLM request failed')


async def photo_features(data: pd.Series) -> pd.Series:
    async with ClientSession(timeout=ClientTimeout(total=60)) as session:
        content = build_content(data['photos'])
        payload = build_payload(content)
        features = await request_vlm(session, payload)
    features = pd.Series(features).reindex(list(QUESTIONS.keys()))
    data.loc[features.index] = features
    return data
