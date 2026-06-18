from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sentinelhub import BBox, CRS, DataCollection, MimeType, SentinelHubRequest, SHConfig

from config import CLIENT_ID, CLIENT_SECRET
from ml.predict import load_model


config = SHConfig()
config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
MODEL_PATH = BASE_DIR / "ml_runs" / "ndvi_cnn" / "ndvi_cnn_model.pth"


def _bbox_from_points(points) -> BBox:
    min_lon = min(p.lon for p in points)
    max_lon = max(p.lon for p in points)
    min_lat = min(p.lat for p in points)
    max_lat = max(p.lat for p in points)

    return BBox(
        bbox=[min_lon, min_lat, max_lon, max_lat],
        crs=CRS.WGS84,
    )


def _status_from_ndvi(value: float) -> str:
    if value < 0.2:
        return "Плохое состояние"
    if value < 0.5:
        return "Среднее состояние"
    return "Хорошее состояние"


def _load_training_metrics() -> dict:
    metrics_path = MODEL_PATH.parent / "metrics.json"

    if not metrics_path.exists():
        return {}

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _fetch_cnn_input_from_sentinel(points, start_date: str, end_date: str) -> tuple[torch.Tensor, np.ndarray]:
    """
    Получает текущие данные Sentinel-2 для выбранного пользователем поля
    и формирует входной тензор CNN в том же порядке, что использовался при обучении:

    Agriculture, Barren_Soil, EVI, Moisture_Index, Moisture_Stress, SAVI, True_Color(R,G,B)
    """

    bbox = _bbox_from_points(points)

    request = SentinelHubRequest(
        evalscript="""
//VERSION=3

function setup() {
  return {
    input: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL", "dataMask"],
    output: {
      bands: 10,
      sampleType: "FLOAT32"
    }
  };
}

function clamp01(x) {
  return Math.max(0.0, Math.min(1.0, x));
}

function normIndex(x) {
  return clamp01((x + 1.0) / 2.0);
}

function safeDiv(a, b) {
  if (Math.abs(b) < 0.000001) {
    return 0.0;
  }
  return a / b;
}

function evaluatePixel(s) {
  var invalid =
    s.dataMask == 0 ||
    s.SCL == 0 ||
    s.SCL == 1 ||
    s.SCL == 2 ||
    s.SCL == 3 ||
    s.SCL == 8 ||
    s.SCL == 9 ||
    s.SCL == 10 ||
    s.SCL == 11;

  if (invalid) {
    return [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  }

  var blue = s.B02;
  var green = s.B03;
  var red = s.B04;
  var nir = s.B08;
  var swir1 = s.B11;
  var swir2 = s.B12;

  var evi = 2.5 * safeDiv((nir - red), (nir + 6.0 * red - 7.5 * blue + 1.0));
  var savi = 1.5 * safeDiv((nir - red), (nir + red + 0.5));

  var barrenSoil = safeDiv(
    ((swir1 + red) - (nir + blue)),
    ((swir1 + red) + (nir + blue))
  );

  var moistureIndex = safeDiv((nir - swir1), (nir + swir1));

  var moistureStressRaw = safeDiv(swir1, nir + 0.0001);
  var moistureStress = clamp01(moistureStressRaw / 2.0);

  var agriculture = safeDiv((nir - swir2), (nir + swir2));

  var trueRed = clamp01(red * 3.5);
  var trueGreen = clamp01(green * 3.5);
  var trueBlue = clamp01(blue * 3.5);

  return [
    normIndex(agriculture),
    normIndex(barrenSoil),
    normIndex(evi),
    normIndex(moistureIndex),
    moistureStress,
    normIndex(savi),
    trueRed,
    trueGreen,
    trueBlue,
    1
  ];
}
        """,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=(start_date, end_date),
                other_args={
                    "dataFilter": {
                        "maxCloudCoverage": 50
                    }
                },
            )
        ],
        responses=[
            SentinelHubRequest.output_response("default", MimeType.TIFF)
        ],
        bbox=bbox,
        size=(180, 120),
        config=config,
    )

    data = request.get_data()[0]

    if data is None or data.ndim != 3 or data.shape[2] < 10:
        raise RuntimeError("Sentinel Hub не вернул данные для CNN")

    features = data[:, :, :9].astype(np.float32)
    valid_mask = data[:, :, 9] > 0

    if not np.any(valid_mask):
        raise RuntimeError("На выбранном участке нет пикселей без облаков для CNN-прогноза")

    features = np.nan_to_num(features, nan=0.0, posinf=1.0, neginf=0.0)
    features = np.clip(features, 0.0, 1.0)

    # H x W x C -> C x H x W
    tensor = torch.from_numpy(np.transpose(features, (2, 0, 1))).float()

    return tensor, valid_mask


@torch.no_grad()
def predict_current_ndvi(points):
    """
    Запускает CNN не на demo-датасете, а на текущем выбранном пользователем поле.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Модель не найдена: {MODEL_PATH}. Сначала обучите CNN."
        )

    end_date = datetime.now()
    start_date = end_date - timedelta(days=20)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    x, valid_mask = _fetch_cnn_input_from_sentinel(points, start_str, end_str)

    model, image_size, device, checkpoint = load_model(MODEL_PATH)

    pred = model(x.unsqueeze(0).to(device)).squeeze().cpu().numpy()
    pred = np.clip(pred, 0.0, 1.0)

    valid_pred = pred[valid_mask]

    if valid_pred.size == 0:
        mean_predicted_ndvi = float(np.mean(pred))
    else:
        mean_predicted_ndvi = float(np.mean(valid_pred))

    STATIC_DIR.mkdir(exist_ok=True)

    output_path = STATIC_DIR / "predicted_ndvi_current.png"

    image_array = np.clip(pred * 255, 0, 255).astype(np.uint8)
    Image.fromarray(image_array).save(output_path)

    metrics = _load_training_metrics()

    result = {
        "image_url": "http://127.0.0.1:8000/static/predicted_ndvi_current.png",
        "mean_predicted_ndvi": round(mean_predicted_ndvi, 6),
        "status": _status_from_ndvi(mean_predicted_ndvi),
        "field": "Выбранный пользователем участок",
        "date_prefix": f"{start_str} — {end_str}",
        "mse": metrics.get("mse"),
        "mae": metrics.get("mae"),
        "r2": metrics.get("r2"),
    }

    return result