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
    pub_year: int | None = None
    pub_month: int | None = None


class SpecificationsBase(BaseModel):
    power: int | None = None
    gear_type: str | None = None
    auto_class: str | None = None


class SpecificationsEngine(BaseModel):
    max_power_kw: int | None = None
    displacement: int | None = None


class SpecificationsSizes(BaseModel):
    tires_rim_min: int | None = None
    width: int | None = None
    height: int | None = None
    disk_x1_min: int | None = None
    wheels_size_x0: int | None = None


class SpecificationsVolume(BaseModel):
    full_weight: int | None = None
    weight: int | None = None


class Specifications(BaseModel):
    base: SpecificationsBase | None = None
    sizes: SpecificationsSizes | None = None
    engine: SpecificationsEngine | None = None
    general: dict[str, dict[str, str]] | None = None
    transmission: dict[str, dict[str, str]] | None = None
    volume_and_mass: SpecificationsVolume | None = None
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
