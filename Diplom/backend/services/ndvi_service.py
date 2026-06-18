from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
from sentinelhub import BBox, CRS, DataCollection, MimeType, SentinelHubRequest, SHConfig

from config import CLIENT_ID, CLIENT_SECRET


config = SHConfig()
config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET


INVALID_SCL_CLASSES = [
    0,   # no data
    1,   # saturated / defective
    2,   # dark area pixels
    3,   # cloud shadows
    8,   # cloud medium probability
    9,   # cloud high probability
    10,  # thin cirrus
    11,  # snow / ice
]


def _bbox_from_points(points) -> BBox:
    min_lon = min(p.lon for p in points)
    max_lon = max(p.lon for p in points)
    min_lat = min(p.lat for p in points)
    max_lat = max(p.lat for p in points)
    return BBox(bbox=[min_lon, min_lat, max_lon, max_lat], crs=CRS.WGS84)


def _status_from_ndvi(mean_ndvi: float) -> str:
    if mean_ndvi < 0.2:
        return "Плохое состояние"
    if mean_ndvi < 0.5:
        return "Среднее состояние"
    return "Хорошее состояние"


def analyze_ndvi(points):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    mean_ndvi = get_ndvi_for_period(
        points,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )

    return {
        "mean_ndvi": mean_ndvi,
        "status": _status_from_ndvi(mean_ndvi),
    }


def get_ndvi_for_period(points, start_date, end_date):
    """
    Рассчитывает средний NDVI по Sentinel-2 L2A.

    Используется SCL-маска, чтобы исключить облака, тени, снег и пиксели без
    данных. Если Sentinel Hub не вернул подходящие пиксели, возвращается 0.0,
    а приложение продолжает работать.
    """
    bbox = _bbox_from_points(points)

    request = SentinelHubRequest(
        evalscript="""
//VERSION=3
function setup() {
  return {
    input: ["B04", "B08", "SCL", "dataMask"],
    output: {
      bands: 4,
      sampleType: "FLOAT32"
    }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B08, sample.SCL, sample.dataMask];
}
        """,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(start_date, end_date),
                other_args={"dataFilter": {"maxCloudCoverage": 30}},
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=bbox,
        size=(256, 256),
        config=config,
    )

    try:
        data = request.get_data()[0]
    except Exception as exc:
        print(f"[ndvi_service] Sentinel Hub не вернул NDVI за {start_date} - {end_date}: {exc}")
        return 0.0

    if data is None or data.ndim != 3 or data.shape[2] < 4:
        print(f"[ndvi_service] Некорректный массив Sentinel Hub за {start_date} - {end_date}")
        return 0.0

    red = data[:, :, 0].astype(np.float32)
    nir = data[:, :, 1].astype(np.float32)
    scl = data[:, :, 2]
    data_mask = data[:, :, 3]

    valid = (
        (data_mask > 0)
        & ~np.isin(scl.astype(np.int16), INVALID_SCL_CLASSES)
        & np.isfinite(red)
        & np.isfinite(nir)
        & ((nir + red) != 0)
    )

    if not np.any(valid):
        print(f"[ndvi_service] Нет валидных пикселей после фильтра облачности за {start_date} - {end_date}")
        return 0.0

    ndvi = (nir[valid] - red[valid]) / (nir[valid] + red[valid])
    mean_ndvi = float(np.nanmean(ndvi))

    if not np.isfinite(mean_ndvi):
        return 0.0

    # NDVI теоретически находится в [-1; 1], но на всякий случай ограничиваем шумы.
    return float(np.clip(mean_ndvi, -1.0, 1.0))
