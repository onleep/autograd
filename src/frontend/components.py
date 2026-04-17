from collections.abc import Sequence
from functools import partial

import altair as alt
import pandas as pd
import streamlit as st

from frontend.data import (
    SPEC_COLUMNS,
    filter_data,
    text_options,
    year_options,
)
from frontend.models import (
    AttributesData,
    OfferData,
    ReadyOffer,
    SimilarStats,
    SpecificationsData,
)
from frontend.pricing import find_similar_group, summarize_similars
from frontend.utils import (
    current_attributes,
    current_offer,
    current_specifications,
    format_money,
    format_number,
    format_option,
    read_text,
    reset_fields,
)


def render_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background-image:
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.16),
                transparent 30%),
                radial-gradient(circle at top left, rgba(249, 115, 22, 0.14),
                transparent 24%);
        }
        .hero-card {
            padding: 1.8rem;
            border-radius: 28px;
            color: white;
            background: linear-gradient(135deg, #0f766e 0%, #f97316 100%);
            box-shadow: 0 22px 45px rgba(15, 23, 42, 0.18);
            margin-bottom: 1rem;
        }
        .stButton > button {
            min-height: 3.1rem;
            border-radius: 999px;
            border: none;
            background: linear-gradient(90deg, #0f766e 0%, #f97316 100%);
            color: white;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(df: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class='hero-card'>
            <h1>🏎️ Прогноз стоимости автомобилей</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(df: pd.DataFrame) -> None:
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric('Объявлений 📚', format_number(len(df)))
    col2.metric('Марок 🏁', int(df['mark'].nunique()))
    col3.metric('Моделей 🧩', int(df['model'].nunique()))
    col4.metric('Поколений 👴', int(df['generation'].nunique()))
    col5.metric('Комлектаций 🛠️', int(df['trim'].nunique()))
    col6.metric('Годы ⏳', f'{int(df["year"].min())} - {int(df["year"].max())}')


def render_form(
    df: pd.DataFrame,
) -> tuple[OfferData, AttributesData | None, SpecificationsData | None]:
    mark = read_text('mark')
    model = read_text('model')
    year = st.session_state.get('year')
    generation = st.session_state.get('generation')
    trim = st.session_state.get('trim')
    model_df = filter_data(df, mark=mark)
    year_df = filter_data(model_df, model=model)
    details_df = filter_data(year_df, year=year)
    trim_df = filter_data(details_df, generation=generation)
    specs_df = filter_data(details_df, generation=generation, trim=trim)
    with st.container(border=True):
        st.subheader('Параметры автомобиля')
        row1 = st.columns(3)
        row2 = st.columns(3)
        with row1[0]:
            st.selectbox(
                '🏷️ Марка',
                text_options(df, 'mark'),
                key='mark',
                index=None,
                placeholder='Начните вводить марку',
                on_change=partial(
                    reset_fields,
                    'model',
                    'year',
                    'generation',
                    'trim',
                    *SPEC_COLUMNS.values(),
                ),
            )
        with row1[1]:
            st.selectbox(
                '🚘 Модель',
                text_options(model_df, 'model'),
                key='model',
                index=None,
                placeholder='Сначала выберите марку',
                disabled=mark is None,
                on_change=partial(
                    reset_fields,
                    'year',
                    'generation',
                    'trim',
                    *SPEC_COLUMNS.values(),
                ),
            )
        with row1[2]:
            st.selectbox(
                '📅 Год',
                year_options(year_df),
                key='year',
                index=None,
                placeholder='Сначала выберите модель',
                disabled=model is None,
                on_change=partial(
                    reset_fields,
                    'generation',
                    'trim',
                    *SPEC_COLUMNS.values(),
                ),
            )
        with row2[0]:
            st.selectbox(
                '✨ Поколение',
                text_options(details_df, 'generation', include_missing=True),
                key='generation',
                index=None,
                placeholder='Можно оставить пустым',
                disabled=year is None,
                on_change=partial(reset_fields, 'trim', *SPEC_COLUMNS.values()),
                format_func=format_option,
            )
        with row2[1]:
            st.selectbox(
                '🎯 Комплектация',
                text_options(trim_df, 'trim', include_missing=True),
                key='trim',
                index=None,
                placeholder='Можно оставить пустым',
                disabled=year is None,
                on_change=partial(reset_fields, *SPEC_COLUMNS.values()),
                format_func=format_option,
            )
        with row2[2]:
            st.number_input(
                '🛣️ Пробег в км',
                min_value=0,
                step=1000,
                key='mileage',
                on_change=reset_fields,
            )
        st.caption('Селекторы формируются исходя из выбранных параметров')
        with st.expander('🔧 Дополнительные характеристики', expanded=False):
            st.caption('Эти поля необязательны, но помогают точнее оценить автомобиль')
            render_optional_fields(df, specs_df, year is None)
    return current_offer(), current_attributes(), current_specifications()


def render_optional_fields(
    attrs_df: pd.DataFrame,
    df: pd.DataFrame,
    disabled: bool,
) -> None:
    st.markdown('**Параметры объявления**')
    row = st.columns(2)
    with row[0]:
        render_optional_select(
            'Регион',
            'region',
            text_options(attrs_df, 'region'),
            disabled,
        )
    with row[1]:
        render_optional_number(
            'Количество владельцев', 'owners', disabled, step=1
        )
    st.markdown('**Базовые характеристики**')
    row = st.columns(3)
    with row[0]:
        render_optional_number(
            'Мощность, л.с.',
            'power',
            disabled,
            step=10,
        )
    with row[1]:
        render_optional_select(
            'Привод', 'gear_type', text_options(df, 'gear_type'), disabled
        )
    with row[2]:
        render_optional_select(
            'Класс автомобиля', 'auto_class', text_options(df, 'auto_class'), disabled
        )
    st.markdown('**Двигатель**')
    row = st.columns(2)
    with row[0]:
        render_optional_number('Мощность, кВт', 'max_power_kw', disabled, step=10)
    with row[1]:
        render_optional_number(
            'Объём двигателя, см³', 'displacement', disabled, step=100
        )
    st.markdown('**Размеры**')
    row = st.columns(3)
    with row[0]:
        render_optional_number('Диаметр диска, дюймы', 'tires_rim_min', disabled)
    with row[1]:
        render_optional_number('Ширина, мм', 'width', disabled, step=10)
    with row[2]:
        render_optional_number('Высота, мм', 'height', disabled, step=10)
    row = st.columns(2)
    with row[0]:
        render_optional_number('Ширина диска, дюймы', 'disk_x1_min', disabled)
    with row[1]:
        render_optional_number('Ширина шин, мм', 'wheels_size_x0', disabled, step=10)
    st.markdown('**Масса**')
    row = st.columns(2)
    with row[0]:
        render_optional_number('Полная масса, кг', 'full_weight', disabled, step=50)
    with row[1]:
        render_optional_number('Снаряжённая масса, кг', 'weight', disabled, step=50)


def render_optional_select(
    label: str,
    key: str,
    options: Sequence[str | int],
    disabled: bool,
) -> None:
    st.selectbox(
        label,
        options,
        key=key,
        index=None,
        placeholder='Можно оставить пустым',
        disabled=disabled or not options,
        on_change=reset_fields,
    )


def render_optional_number(
    label: str,
    key: str,
    disabled: bool,
    step: int = 1,
) -> None:
    st.number_input(
        label,
        key=key,
        value=None,
        min_value=0,
        step=step,
        disabled=disabled,
        on_change=reset_fields,
    )


def render_result(df: pd.DataFrame, offer: ReadyOffer, price: float) -> None:
    similars, scope = find_similar_group(df, offer)
    stats = summarize_similars(similars, offer, price)
    st.subheader('Результат прогноза')
    render_metrics(price, stats, scope)
    charts = st.columns(2)
    with charts[0]:
        render_history_chart(df, offer)
    with charts[1]:
        render_similar_chart(similars, offer, price)


def render_metrics(price: float, stats: SimilarStats, scope: str) -> None:
    col1, col2, col3 = st.columns(3)
    col1.metric(
        'Средний пробег 🛞',
        format_number(stats['avg_mileage']) + ' км',
        delta=format_number(stats['mileage_gap']) + ' км',
        delta_color='inverse',
    )
    col2.metric(
        'Медиана рынка 📊',
        format_money(stats['median_price']),
        delta=format_money(stats['price_gap']),
        delta_color='inverse',
    )
    col3.metric('Прогноз цены 💰', format_money(price))
    render_insights(stats, scope)


def render_insights(stats: SimilarStats, scope: str) -> None:
    row = st.columns(3)
    price_word = 'дешевле' if stats['price_gap'] < 0 else 'дороже'
    mileage_word = 'ниже' if stats['mileage_gap'] < 0 else 'выше'
    insights = [
        (
            '💸 Цена',
            f'Авто на {format_money(abs(stats["price_gap"]))} {price_word} '
            f'среднего по {scope}',
        ),
        (
            '🛣️ Пробег',
            f'Пробег на {format_number(abs(stats["mileage_gap"]))} км '
            f'{mileage_word} среднего и лучше, чем у '
            f'{stats["lower_mileage_share"]:.0f}% похожих машин',
        ),
        (
            '📈 Рынок',
            f'Сравнение построено по {format_number(stats["count"])} '
            f'объявлениям, а цена ниже, чем у '
            f'{stats["cheaper_share"]:.0f}% рынка',
        ),
    ]
    for column, (title, text) in zip(row, insights, strict=True):
        with column:
            with st.container(border=True, height='stretch'):
                st.caption(title)
                st.write(text)


def render_history_chart(df: pd.DataFrame, offer: ReadyOffer) -> None:
    history = filter_data(df, mark=offer['mark'], model=offer['model'])
    history = history.groupby('year', as_index=False)['price'].median()
    focus = history[history['year'] == offer['year']]
    with st.container(border=True, height='stretch'):
        st.caption('📉 Динамика цены по годам')
        if len(history) < 2:
            st.info('Для этой машины мало данных чтобы показать график по годам')
            return
        trend = (
            alt.Chart(history)
            .mark_line(point=True)
            .properties(height=300)
            .encode(
                x=alt.X('year:O', title='Год'),
                y=alt.Y('price:Q', title='Медианная цена в ₽'),
                tooltip=['year:O', alt.Tooltip('price:Q', format=',.0f')],
            )
        )
        chart = trend
        if not focus.empty:
            selected = (
                alt.Chart(focus)
                .mark_point(color='#f97316', filled=True, shape='diamond', size=240)
                .encode(x='year:O', y='price:Q')
            )
            chart = trend + selected
        st.altair_chart(chart, width='stretch')


def render_similar_chart(
    similars: pd.DataFrame,
    offer: ReadyOffer,
    price: float,
) -> None:
    with st.container(border=True, height='stretch'):
        st.caption('🎯 Прогноз на фоне похожих объявлений')
        if similars.empty:
            st.info(
                'Для этой машины мало данных чтобы показать график похожих объявлений'
            )
            return
        sample = similars.sample(min(len(similars), 500), random_state=42)
        focus = pd.DataFrame([{'mileage': offer['mileage'], 'price': price}])
        points = (
            alt.Chart(sample)
            .mark_circle(color='#0f766e', opacity=0.32, size=70)
            .encode(
                x=alt.X('mileage:Q', title='Пробег в км'),
                y=alt.Y('price:Q', title='Цена в ₽'),
                tooltip=['mileage:Q', alt.Tooltip('price:Q', format=',.0f')],
            )
        )
        prediction = (
            alt.Chart(focus)
            .mark_point(color='#f97316', filled=True, shape='diamond', size=240)
            .encode(x='mileage:Q', y='price:Q')
        )
        st.altair_chart(
            (points + prediction).properties(height=320).interactive(),
            width='stretch',
        )
