from datetime import datetime

import pandas as pd
import requests

from config import API_ADDR
from frontend.data import filter_data
from frontend.models import (
    AttributesData,
    PeerStats,
    PeerTier,
    ReadyOffer,
    SpecificationsData,
)


def predict_price(
    offer: ReadyOffer,
    specifications: SpecificationsData | None = None,
) -> float:
    response = requests.post(
        API_ADDR,
        json={
            'data': {
                'offer': offer,
                'attributes': get_attrs(),
                'specifications': specifications,
            }
        },
        timeout=10,
    )
    response.raise_for_status()
    return float(response.json()['price'])


def get_attrs() -> AttributesData:
    now = datetime.now().astimezone()
    return {'pub_year': now.year, 'pub_month': now.month}


def build_peer_tiers(offer: ReadyOffer) -> list[PeerTier]:
    def pick(*keys: str) -> dict[str, str | int | None]:
        return {key: offer[key] for key in keys}

    tiers: list[PeerTier] = []
    default = ('mark', 'model', 'year')
    if offer['trim']:
        tiers.append((pick(*default, 'generation', 'trim'), 12, 'этой же комплектации'))
    if offer['generation']:
        tiers.append((pick(*default, 'generation'), 18, 'этой же генерации'))
    tiers.extend(
        [
            (pick(*default), 25, 'этой же модели и года'),
            (pick('mark', 'model'), 40, 'этой же модели'),
            ({'mark': offer['mark']}, 80, 'этой марки'),
        ]
    )
    return tiers


def find_peer_group(
    df: pd.DataFrame,
    offer: ReadyOffer,
) -> tuple[pd.DataFrame, str]:
    fallback = filter_data(df, mark=offer['mark'])
    label = 'этой марки'
    for filters, min_rows, tier_label in build_peer_tiers(offer):
        peers = filter_data(df, **filters)
        if not peers.empty:
            fallback = peers
            label = tier_label
        if len(peers) >= min_rows:
            return peers, tier_label
    return fallback, label


def summarize_peers(
    peers: pd.DataFrame,
    offer: ReadyOffer,
    price: float,
) -> PeerStats:
    median_price = float(peers['price'].median())
    avg_mileage = float(peers['mileage'].mean())
    return {
        'count': float(len(peers)),
        'median_price': median_price,
        'avg_mileage': avg_mileage,
        'price_gap': float(price - median_price),
        'mileage_gap': float(float(offer['mileage']) - avg_mileage),
        'cheaper_share': float((peers['price'] > price).mean() * 100),
        'lower_mileage_share': float(
            (peers['mileage'] > offer['mileage']).mean() * 100
        ),
    }
