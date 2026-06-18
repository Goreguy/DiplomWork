from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch
from PIL import Image

from ml.dataset import INDEX_INPUTS, TARGET_INDEX, SampleItem, discover_samples, load_input_tensor, load_target_tensor
from ml.model import MultiScaleNDVICNN
from ml.train import r2_score_torch


def _status_from_normalized_ndvi(value: float) -> str:
    # Значение здесь нормировано по изображению [0; 1], поэтому это приближенная оценка.
    if value < 0.2:
        return "Плохое состояние"
    if value < 0.5:
        return "Среднее состояние"
    return "Хорошее состояние"


def load_model(model_path: str | Path, device: Optional[torch.device] = None):
    model_path = Path(model_path)
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    checkpoint = torch.load(model_path, map_location=device)
    model = MultiScaleNDVICNN(in_channels=checkpoint.get("in_channels", 9)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    image_size = tuple(checkpoint.get("image_size", [180, 120]))
    return model, image_size, device, checkpoint


def find_sample(data_dirs: list[str | Path], date_prefix: str | None = None) -> SampleItem:
    samples = discover_samples(data_dirs)
    if date_prefix is None:
        return samples[-1]

    for item in samples:
        if item.date_prefix.startswith(date_prefix) or item.date_prefix == date_prefix:
            return item

    raise ValueError(f"Дата не найдена в датасете: {date_prefix}")


@torch.no_grad()
def predict_sample(
    model_path: str | Path,
    data_dirs: list[str | Path],
    output_path: str | Path,
    date_prefix: str | None = None,
) -> Dict[str, float | str]:
    model, image_size, device, _ = load_model(model_path)
    item = find_sample(data_dirs, date_prefix=date_prefix)

    x = load_input_tensor(item.files, image_size)
    pred = model(x.unsqueeze(0).to(device)).squeeze().cpu()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    arr = np.clip(pred.numpy() * 255, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(output_path)

    mean_value = float(pred.mean().item())
    result: Dict[str, float | str] = {
        "field": item.field_name,
        "date_prefix": item.date_prefix,
        "predicted_image": str(output_path),
        "mean_predicted_ndvi": mean_value,
        "status": _status_from_normalized_ndvi(mean_value),
    }

    if TARGET_INDEX in item.files:
        y = load_target_tensor(item.files, image_size)
        mse = torch.mean((pred.unsqueeze(0) - y) ** 2).item()
        mae = torch.mean(torch.abs(pred.unsqueeze(0) - y)).item()
        r2 = r2_score_torch(y, pred.unsqueeze(0))
        result.update({"mse": float(mse), "mae": float(mae), "r2": float(r2)})

    return result
