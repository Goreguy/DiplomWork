from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from sentinelhub import BBox, CRS, DataCollection, MimeType, SentinelHubRequest, SHConfig

from config import CLIENT_ID, CLIENT_SECRET


config = SHConfig()
config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET

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


def _save_empty_rgb(path: Path) -> None:
    Image.fromarray(np.full((512, 512, 3), 220, dtype=np.uint8)).save(path)


def generate_rgb_image(points, start_date, end_date):
    bbox, size = _bbox_and_size(points)

    request = SentinelHubRequest(
        evalscript="""
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02", "dataMask"],
    output: { bands: 4, sampleType: "FLOAT32" }
  };
}

function evaluatePixel(s) {
  return [s.B04, s.B03, s.B02, s.dataMask];
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
    output_path = STATIC_DIR / "rgb.png"

    try:
        data = request.get_data()[0]
    except Exception as exc:
        print(f"[rgb_service] Sentinel Hub не вернул RGB: {exc}")
        _save_empty_rgb(output_path)
        return "/static/rgb.png"

    if data is None or data.ndim != 3 or data.shape[2] < 4:
        _save_empty_rgb(output_path)
        return "/static/rgb.png"

    rgb = data[:, :, :3].astype(np.float32)
    mask = data[:, :, 3] > 0

    if not np.any(mask):
        _save_empty_rgb(output_path)
        return "/static/rgb.png"

    valid_pixels = rgb[mask]
    p2 = np.percentile(valid_pixels, 2)
    p98 = np.percentile(valid_pixels, 98)

    rgb = np.clip(rgb, p2, p98)
    rgb = (rgb - p2) / (p98 - p2 + 1e-6)
    rgb = np.clip(rgb * 255, 0, 255).astype(np.uint8)

    Image.fromarray(rgb).save(output_path)
    return "/static/rgb.png"
