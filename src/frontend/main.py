import requests
import streamlit as st

from frontend.components import (
    render_form,
    render_header,
    render_overview,
    render_result,
    render_styles,
)
from frontend.data import load_data
from frontend.models import is_offer_ready
from frontend.pricing import predict_price
from frontend.utils import init_state


def main() -> None:
    st.set_page_config(page_title='Car Price Predictor', page_icon='🏎️', layout='wide')
    init_state()
    render_styles()
    data = load_data()
    render_header(data)
    render_overview(data)
    # st.caption(f'API endpoint: `{API_ADDR}`')
    offer, attributes, photos, specifications = render_form(data)
    if st.button('Предсказать стоимость 💸', type='primary', width='stretch'):
        if not is_offer_ready(offer):
            st.warning('Сначала выберите марку, модель и год автомобиля')
        else:
            with st.spinner('Считаю стоимость и сравниваю с рынком...'):
                try:
                    st.session_state['prediction'] = predict_price(
                        offer,
                        photos,
                        attributes,
                        specifications,
                    )
                except requests.RequestException as error:
                    st.error(f'Не получилось обратиться к API: {error}')
                else:
                    st.toast('Прогноз готов. Можно изучать рынок ✨')
    prediction = st.session_state.get('prediction')
    if isinstance(prediction, (int, float)) and is_offer_ready(offer):
        render_result(data, offer, float(prediction))


if __name__ == '__main__':
    main()
