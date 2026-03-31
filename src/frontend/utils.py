import streamlit as st

from frontend.data import MISSING
from frontend.models import (
    OfferData,
    SpecificationsBaseData,
    SpecificationsData,
    SpecificationsEngineData,
    SpecificationsSizesData,
    SpecificationsVolumeData,
)


def format_money(value: float | int) -> str:
    return f'{round(float(value)):,.0f}'.replace(',', ' ') + ' ₽'


def format_number(value: float | int) -> str:
    return f'{value:,.0f}'.replace(',', ' ')


def format_option(value: str | int | None) -> str:
    if value == MISSING: return 'Не указано'  # fmt: off
    return str(value)


def init_state() -> None:
    defaults = {
        'mark': None,
        'model': None,
        'year': None,
        'generation': None,
        'trim': None,
        'mileage': 60000,
        'power': None,
        'gear_type': None,
        'auto_class': None,
        'max_power_kw': None,
        'displacement': None,
        'tires_rim_min': None,
        'width': None,
        'height': None,
        'disk_x1_min': None,
        'wheels_size_x0': None,
        'full_weight': None,
        'weight': None,
        'prediction': None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_fields(*keys: str) -> None:
    for key in keys:
        st.session_state[key] = None
    st.session_state['prediction'] = None


def current_offer() -> OfferData:
    year = st.session_state.get('year')
    mileage = st.session_state.get('mileage', 0)
    return {
        'mark': read_text('mark'),
        'model': read_text('model'),
        'year': year if isinstance(year, int) else None,
        'generation': normalize_text('generation'),
        'trim': normalize_text('trim'),
        'mileage': int(mileage) if isinstance(mileage, (int, float)) else 0,
    }


def current_specifications() -> SpecificationsData | None:
    specifications: SpecificationsData = {}
    base = read_base_specifications()
    engine = read_engine_specifications()
    sizes = read_sizes_specifications()
    volume = read_volume_specifications()
    if base:
        specifications['base'] = base
    if engine:
        specifications['engine'] = engine
    if sizes:
        specifications['sizes'] = sizes
    if volume:
        specifications['volume_and_mass'] = volume
    return specifications or None


def read_text(key: str) -> str | None:
    value = st.session_state.get(key)
    return value if isinstance(value, str) else None


def normalize_text(key: str) -> str | None:
    value = read_text(key)
    return None if value == MISSING else value


def read_int(key: str) -> int | None:
    value = st.session_state.get(key)
    return int(value) if isinstance(value, (int, float)) else None


def read_base_specifications() -> SpecificationsBaseData:
    specification: SpecificationsBaseData = {}
    power = read_int('power')
    gear_type = read_text('gear_type')
    auto_class = read_text('auto_class')
    if power is not None:
        specification['power'] = power
    if gear_type is not None:
        specification['gear_type'] = gear_type
    if auto_class is not None:
        specification['auto_class'] = auto_class
    return specification


def read_engine_specifications() -> SpecificationsEngineData:
    specification: SpecificationsEngineData = {}
    max_power_kw = read_int('max_power_kw')
    displacement = read_int('displacement')
    if max_power_kw is not None:
        specification['max_power_kw'] = max_power_kw
    if displacement is not None:
        specification['displacement'] = displacement
    return specification


def read_sizes_specifications() -> SpecificationsSizesData:
    specification: SpecificationsSizesData = {}
    tires_rim_min = read_int('tires_rim_min')
    width = read_int('width')
    height = read_int('height')
    disk_x1_min = read_int('disk_x1_min')
    wheels_size_x0 = read_int('wheels_size_x0')
    if tires_rim_min is not None:
        specification['tires_rim_min'] = tires_rim_min
    if width is not None:
        specification['width'] = width
    if height is not None:
        specification['height'] = height
    if disk_x1_min is not None:
        specification['disk_x1_min'] = disk_x1_min
    if wheels_size_x0 is not None:
        specification['wheels_size_x0'] = wheels_size_x0
    return specification


def read_volume_specifications() -> SpecificationsVolumeData:
    specification: SpecificationsVolumeData = {}
    full_weight = read_int('full_weight')
    weight = read_int('weight')
    if full_weight is not None:
        specification['full_weight'] = full_weight
    if weight is not None:
        specification['weight'] = weight
    return specification
