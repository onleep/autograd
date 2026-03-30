from typing import Any

from catboost import CatBoostRegressor
from pydantic import BaseModel
from sklearn.preprocessing import MultiLabelBinarizer


class AppState(BaseModel):
    model: CatBoostRegressor
    mlb_quip: MultiLabelBinarizer
    mlb_tags: MultiLabelBinarizer

    class Config:
        arbitrary_types_allowed = True


class Offer(BaseModel):
    mark: str
    model: str
    year: int
    mileage: int
    trim: str | None = None
    generation: str | None = None


class Attributes(BaseModel):
    color: str | None = None
    owners: int | None = None
    region: str | None = None
    tags: list[str] | None = None
    description: str | None = None
    vin: dict[str, Any] | None = None
    equipment: list[str] | None = None


class Specifications(BaseModel):
    base: dict[str, dict[str, str]] | None = None
    sizes: dict[str, dict[str, str]] | None = None
    engine: dict[str, dict[str, str]] | None = None
    general: dict[str, dict[str, str]] | None = None
    transmission: dict[str, dict[str, str]] | None = None
    volume_and_mass: dict[str, dict[str, str]] | None = None
    suspension_and_brakes: dict[str, dict[str, str]] | None = None
    performance_indicators: dict[str, dict[str, str]] | None = None


class PredictData(BaseModel):
    offer: Offer
    attributes: Attributes | None = None
    specifications: Specifications | None = None


class PredictReq(BaseModel):
    data: PredictData


class PredictResp(BaseModel):
    price: float
