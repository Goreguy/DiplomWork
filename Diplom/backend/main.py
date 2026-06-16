from fastapi import FastAPI

from models.polygon_model import PolygonRequest

from services.ndvi_service import analyze_ndvi
from services.history_service import get_ndvi_history
from fastapi.staticfiles import StaticFiles
from services.heatmap_service import generate_ndvi_heatmap
from datetime import datetime, timedelta
from services.rgb_service import generate_rgb_image


app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


@app.post("/analyze")
async def analyze(data: PolygonRequest):

    result = analyze_ndvi(data.points)

    return result

@app.post("/history")
async def history(data: PolygonRequest):

    return {
        "history": get_ndvi_history(data.points)
    }

@app.post("/heatmap")
async def heatmap(data: PolygonRequest):

    end_date = datetime.now()

    start_date = end_date - timedelta(days=7)

    generate_ndvi_heatmap(
        data.points,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    return {
        "image_url": "http://127.0.0.1:8000/static/ndvi_heatmap.png"
    }

@app.post("/rgb")
async def rgb(data: PolygonRequest):

    end_date = datetime.now()

    start_date = end_date - timedelta(days=7)

    generate_rgb_image(
        data.points,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    return {
        "image_url": "http://127.0.0.1:8000/static/rgb.png"
    }