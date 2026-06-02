from pydantic import BaseModel

from typing import List


class Point(BaseModel):
    lat: float
    lon: float


class PolygonRequest(BaseModel):
    points: List[Point]