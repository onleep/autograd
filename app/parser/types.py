from typing import TypedDict

from aiohttp import ClientResponse, ClientSession


class Response(TypedDict):
    data: ClientResponse
    json: dict | None
    text: str | None
    raw: bytes | None


class ProxyData(TypedDict):
    cooldown: float
    errors: int
    lock: bool
    session: ClientSession | None


class Fingerpring(TypedDict):
    headers: dict[str, str]
    layout: dict[str, int]


class ListInfo(TypedDict):
    custom_cleared: bool
    price: float
    mileage: int
    owners: int
    model: str
    year: int
    mark: str
    region: str | None
    photos: dict[str, str]
    tags: list[str] | None
    predicted_prices: dict[str, dict] | None


class ExtListInfo(ListInfo):
    autoru_hash: str
    published_at: str
    color: str | None
    description: str | None


class PageInfo(TypedDict):
    published_at: str
    color: str | None
    description: str | None


class TechInfo(TypedDict):
    performance_indicators: dict[str, dict[str, str]] | None
    transmission: dict[str, dict[str, str]] | None
    base: dict[str, dict[str, str]] | None
    sizes: dict[str, dict[str, str]] | None
    engine: dict[str, dict[str, str]] | None
    general: dict[str, dict[str, str]] | None
    volume_and_mass: dict[str, dict[str, str]] | None
    suspension_and_brakes: dict[str, dict[str, str]] | None
