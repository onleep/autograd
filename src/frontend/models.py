from typing import TypedDict, TypeGuard

SimilarFilters = dict[str, str | int | None]
SimilarTier = tuple[SimilarFilters, int, str]


class OfferData(TypedDict):
    mark: str | None
    model: str | None
    year: int | None
    generation: str | None
    trim: str | None
    mileage: int


class ReadyOffer(TypedDict):
    mark: str
    model: str
    year: int
    generation: str | None
    trim: str | None
    mileage: int


class SimilarStats(TypedDict):
    count: float
    median_price: float
    avg_mileage: float
    price_gap: float
    mileage_gap: float
    cheaper_share: float
    lower_mileage_share: float


class SpecificationsBaseData(TypedDict, total=False):
    power: int
    gear_type: str
    auto_class: str


class SpecificationsEngineData(TypedDict, total=False):
    max_power_kw: int
    displacement: int


class SpecificationsSizesData(TypedDict, total=False):
    tires_rim_min: int
    width: int
    height: int
    disk_x1_min: int
    wheels_size_x0: int


class SpecificationsVolumeData(TypedDict, total=False):
    full_weight: int
    weight: int


class SpecificationsData(TypedDict, total=False):
    base: SpecificationsBaseData
    engine: SpecificationsEngineData
    sizes: SpecificationsSizesData
    volume_and_mass: SpecificationsVolumeData


class AttributesData(TypedDict):
    pub_year: int
    pub_month: int


def is_offer_ready(offer: OfferData | ReadyOffer) -> TypeGuard[ReadyOffer]:
    return (
        offer['mark'] is not None
        and offer['model'] is not None
        and offer['year'] is not None
    )
