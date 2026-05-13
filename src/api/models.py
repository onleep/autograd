import base64
from typing import Annotated, Any

import pandas as pd
from catboost import CatBoostRegressor
from pydantic import BaseModel, Field, field_validator
from sklearn.preprocessing import MultiLabelBinarizer


class AppState(BaseModel):
    model: CatBoostRegressor
    mlb_quip: MultiLabelBinarizer
    mlb_tags: MultiLabelBinarizer
    aggs_df: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True


class Offer(BaseModel):
    mark: str
    model: str
    year: int
    mileage: int
    trim: str | None = None
    generation: str | None = None


class Photos(BaseModel):
    photos: Annotated[list[str], Field(max_length=5)] | None = None
    body_condition: int | None = None
    photo_quality: int | None = None
    car_cleanliness: int | None = None
    rust_presence: bool | None = None
    glass_condition: int | None = None
    damage_severity: int | None = None
    paint_condition: int | None = None
    wheel_condition: int | None = None

    @field_validator('photos')
    @classmethod
    def validate_photos(cls, value: list[str] | None) -> list[str] | None:
        if value is None: return value  # fmt: off
        for photo in value:
            try:
                base64.b64decode(photo, validate=True)
            except Exception as e:
                raise ValueError('Photo must be valid base64') from e
        return value


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
    tags_equitable_price: int | None = 1
    tags_increased_price: int | None = 0


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
    photos: Photos = Field(default_factory=Photos)
    attributes: Attributes = Field(default_factory=Attributes)
    specifications: Specifications = Field(default_factory=Specifications)


class PredictReq(BaseModel):
    data: PredictData


class PredictResp(BaseModel):
    price: float
