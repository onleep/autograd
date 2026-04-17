from datetime import datetime

import pandas as pd
import requests

from config import API_ADDR
from frontend.data import filter_data
from frontend.models import (
    AttributesData,
    ReadyOffer,
    SimilarStats,
    SimilarTier,
    SpecificationsData,
)


def predict_price(
    offer: ReadyOffer,
    attributes: AttributesData | None = None,
    specifications: SpecificationsData | None = None,
) -> float:
    response = requests.post(
        API_ADDR,
        json={
            'data': {
                'offer': offer,
                'attributes': get_attrs(attributes),
                'specifications': specifications,
            }
        },
        timeout=10,
    )
    response.raise_for_status()
    return float(response.json()['price'])


def get_attrs(attributes: AttributesData | None = None) -> AttributesData:
    now = datetime.now().astimezone()
    payload: AttributesData = {'pub_year': now.year, 'pub_month': now.month}
    if attributes is None:
        return payload
    if 'region' in attributes:
        payload['region'] = attributes['region']
    if 'owners' in attributes:
        payload['owners'] = attributes['owners']
    return payload


def build_similar_tiers(offer: ReadyOffer) -> list[SimilarTier]:
    def pick(*keys: str) -> dict[str, str | int | None]:
        return {key: offer[key] for key in keys}

    MIN_OFFERS = 10
    tiers: list[SimilarTier] = []
    default = ('mark', 'model', 'year')
    if offer['generation'] and offer['trim']:
        tiers.append(
            (
                pick(*default, 'generation', 'trim'),
                MIN_OFFERS,
                'этого же поколения и комплектации',
            )
        )
    if offer['generation']:
        tiers.append((pick(*default, 'generation'), MIN_OFFERS, 'этого же поколения'))
    if offer['trim']:
        tiers.append((pick(*default, 'trim'), MIN_OFFERS, 'этой же комплектации'))
    tiers.append((pick(*default), MIN_OFFERS, 'этой же модели и года'))
    return tiers


def find_similar_group(
    df: pd.DataFrame,
    offer: ReadyOffer,
) -> tuple[pd.DataFrame, str]:
    fallback = pd.DataFrame()
    label = 'этой же модели и года'
    for filters, min_rows, tier_label in build_similar_tiers(offer):
        similars = filter_data(df, **filters)
        if not similars.empty:
            fallback = similars
            label = tier_label
        if len(similars) >= min_rows:
            return similars, tier_label
    return fallback, label


def summarize_similars(
    similars: pd.DataFrame,
    offer: ReadyOffer,
    price: float,
) -> SimilarStats:
    median_price = float(similars['price'].median())
    avg_mileage = float(similars['mileage'].mean())
    return {
        'count': float(len(similars)),
        'median_price': median_price,
        'avg_mileage': avg_mileage,
        'price_gap': float(price - median_price),
        'mileage_gap': float(float(offer['mileage']) - avg_mileage),
        'cheaper_share': float((similars['price'] > price).mean() * 100),
        'lower_mileage_share': float(
            (similars['mileage'] > offer['mileage']).mean() * 100
        ),
    }
