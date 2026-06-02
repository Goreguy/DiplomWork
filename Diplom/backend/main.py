from fastapi import FastAPI

from models.polygon_model import PolygonRequest

from services.ndvi_service import analyze_ndvi


app = FastAPI()


@app.post("/analyze")
async def analyze(data: PolygonRequest):

    result = analyze_ndvi(data.points)

    return result