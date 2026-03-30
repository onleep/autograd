import numpy as np
import uvicorn
from fastapi import FastAPI, Request

from .models import AppState, PredictReq, PredictResp
from .preprocess import load_model, prepredict

app = FastAPI()


@app.post('/predict', response_model=PredictResp)
async def prediction(body: PredictReq, request: Request):
    state: AppState = request.app.state.ctx
    data = prepredict(body.data.model_dump(), state)
    return {'price': np.expm1(state.model.predict(data)).item()}


async def fastapi():
    model, mlb_quip, mlb_tags = await load_model()
    app.state.ctx = AppState(
        model=model,
        mlb_quip=mlb_quip,
        mlb_tags=mlb_tags,
    )
    config = uvicorn.Config(app, host='0.0.0.0', log_config=None)
    await uvicorn.Server(config).serve()
