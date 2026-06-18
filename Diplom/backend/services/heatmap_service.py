from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sentinelhub import BBox, CRS, DataCollection, MimeType, SentinelHubRequest, SHConfig

from config import CLIENT_ID, CLIENT_SECRET


config = SHConfig()
config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET

INVALID_SCL_CLASSES = [0, 1, 2, 3, 8, 9, 10, 11]
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


def _bbox_and_size(points, base: int = 512):
    min_lon = min(p.lon for p in points)
    max_lon = max(p.lon for p in points)
    min_lat = min(p.lat for p in points)
    max_lat = max(p.lat for p in points)

    bbox = BBox(bbox=[min_lon, min_lat, max_lon, max_lat], crs=CRS.WGS84)

    width = max(max_lon - min_lon, 1e-9)
    height = max(max_lat - min_lat, 1e-9)
    ratio = width / height

    if ratio > 1:
        size = (base, max(1, int(base / ratio)))
    else:
        size = (max(1, int(base * ratio)), base)

    return bbox, size


def _save_empty_heatmap(path: Path, message: str = "Нет данных") -> None:
    plt.figure(figsize=(8, 6))
    plt.imshow(np.zeros((120, 180), dtype=np.float32), cmap="RdYlGn", vmin=-1, vmax=1)
    plt.title(message)
    plt.colorbar(label="NDVI")
    plt.axis("off")
    plt.savefig(path, bbox_inches="tight")
    plt.close()


def generate_ndvi_heatmap(points, start_date, end_date):
    bbox, size = _bbox_and_size(points)

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
        size=size,
        config=config,
    )

    STATIC_DIR.mkdir(exist_ok=True)
    output_path = STATIC_DIR / "ndvi_heatmap.png"

    try:
        data = request.get_data()[0]
    except Exception as exc:
        print(f"[heatmap_service] Sentinel Hub не вернул heatmap: {exc}")
        _save_empty_heatmap(output_path, "Нет снимка Sentinel-2")
        return "/static/ndvi_heatmap.png"

    if data is None or data.ndim != 3 or data.shape[2] < 4:
        _save_empty_heatmap(output_path, "Нет данных")
        return "/static/ndvi_heatmap.png"

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

    ndvi = np.full(red.shape, np.nan, dtype=np.float32)
    ndvi[valid] = (nir[valid] - red[valid]) / (nir[valid] + red[valid])

    if not np.any(valid):
        _save_empty_heatmap(output_path, "Нет пикселей без облаков")
        return "/static/ndvi_heatmap.png"

    plt.figure(figsize=(8, 6))
    plt.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    plt.colorbar(label="NDVI")
    plt.axis("off")
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()

    return "/static/ndvi_heatmap.png"
