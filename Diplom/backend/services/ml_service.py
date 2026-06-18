from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from ml.predict import predict_sample

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
MODEL_PATH = BASE_DIR / "ml_runs" / "ndvi_cnn" / "ndvi_cnn_model.pth"


def _read_dataset_dirs() -> list[str]:
    """
    Читает пути к папкам датасета из переменной окружения CNN_DATASET_DIRS.
    На Windows несколько путей указываются через точку с запятой:
    set CNN_DATASET_DIRS=D:\\dataset\\field_1;D:\\dataset\\field_2
    """
    raw = os.getenv("CNN_DATASET_DIRS", "").strip()
    if raw:
        return [item.strip().strip('"') for item in raw.split(";") if item.strip()]

    # Запасной вариант: если пользователь добавит DATASET_DIRS в backend/config.py
    try:
        from config import DATASET_DIRS  # type: ignore

        if isinstance(DATASET_DIRS, (list, tuple)) and DATASET_DIRS:
            return [str(item) for item in DATASET_DIRS]
    except Exception:
        pass

    raise RuntimeError(
        "Не указаны папки датасета. Задайте переменную окружения CNN_DATASET_DIRS "
        "или добавьте DATASET_DIRS = [r'путь_к_папке_1', r'путь_к_папке_2'] в backend/config.py"
    )


def predict_ndvi_demo(date_prefix: Optional[str] = None):
    """
    Запускает обученную CNN-модель на одном примере из подготовленного датасета.
    Используется для вывода результата ML-модуля в интерфейсе приложения.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Модель не найдена: {MODEL_PATH}. "
            "Сначала обучите CNN: python -m ml.train --data-dirs ..."
        )

    data_dirs = _read_dataset_dirs()

    STATIC_DIR.mkdir(exist_ok=True)
    output_path = STATIC_DIR / "predicted_ndvi.png"

    result = predict_sample(
        model_path=MODEL_PATH,
        data_dirs=data_dirs,
        output_path=output_path,
        date_prefix=date_prefix,
    )

    # cache-buster добавит Flutter, здесь возвращаем постоянный URL
    result["image_url"] = "http://127.0.0.1:8000/static/predicted_ndvi.png"
    return result
