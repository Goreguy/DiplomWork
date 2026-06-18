from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from models.polygon_model import PolygonRequest
from services.heatmap_service import generate_ndvi_heatmap
from services.history_service import get_ndvi_history
from services.ndvi_service import analyze_ndvi
from services.rgb_service import generate_rgb_image


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


@app.post("/analyze")
async def analyze(data: PolygonRequest):
    try:
        return analyze_ndvi(data.points)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка анализа NDVI: {e}"},
        )


@app.post("/history")
async def history(data: PolygonRequest):
    # get_ndvi_history сам обрабатывает частичные ошибки по погоде/NDVI,
    # поэтому endpoint не должен падать из-за одного проблемного периода.
    try:
        return {"history": get_ndvi_history(data.points)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка формирования истории NDVI: {e}"},
        )


@app.post("/heatmap")
async def heatmap(data: PolygonRequest):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        generate_ndvi_heatmap(
            data.points,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )

        return {"image_url": "http://127.0.0.1:8000/static/ndvi_heatmap.png"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка построения NDVI-карты: {e}"},
        )


@app.post("/rgb")
async def rgb(data: PolygonRequest):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        generate_rgb_image(
            data.points,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )

        return {"image_url": "http://127.0.0.1:8000/static/rgb.png"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ошибка получения RGB-снимка: {e}"},
        )


@app.get("/ml/predict-demo")
async def ml_predict_demo(date_prefix: str | None = None):
    """
    Демонстрационный endpoint CNN-модуля.
    Возвращает реконструированную NDVI-карту по одному примеру из датасета.
    """
    try:
        from services.ml_service import predict_ndvi_demo

        return predict_ndvi_demo(date_prefix=date_prefix)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )

@app.post("/ml/predict-current")
async def ml_predict_current(data: PolygonRequest):
    """
    CNN-прогноз NDVI для выбранного пользователем поля.
    """
    try:
        from services.ml_current_service import predict_current_ndvi

        return predict_current_ndvi(data.points)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )