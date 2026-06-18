from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

# NDVI используется как целевой слой, поэтому в признаки его не включаем.
INDEX_INPUTS = [
    "Agriculture",
    "Barren_Soil",
    "EVI",
    "Moisture_Index",
    "Moisture_Stress",
    "SAVI",
    "True_Color",
]
TARGET_INDEX = "NDVI"


@dataclass(frozen=True)
class SampleItem:
    field_name: str
    date_prefix: str
    files: Dict[str, Path]


def _parse_sentinel_filename(path: Path) -> Tuple[str, str] | None:
    """
    Пример имени:
    2024-04-01-00_00_2024-04-01-23_59_Sentinel-2_L2A_NDVI.png
    Возвращает (date_prefix, index_name).
    """
    marker = "_Sentinel-2_L2A_"
    stem = path.stem
    if marker not in stem:
        return None
    date_prefix, index_name = stem.split(marker, 1)
    return date_prefix, index_name


def discover_samples(data_dirs: Sequence[str | Path]) -> List[SampleItem]:
    """Группирует файлы по папке и дате наблюдения."""
    samples: List[SampleItem] = []

    required = set(INDEX_INPUTS + [TARGET_INDEX])

    for data_dir in data_dirs:
        root = Path(data_dir)
        if not root.exists():
            raise FileNotFoundError(f"Папка датасета не найдена: {root}")

        grouped: Dict[str, Dict[str, Path]] = {}
        for file_path in sorted(root.glob("*.png")):
            parsed = _parse_sentinel_filename(file_path)
            if parsed is None:
                continue

            date_prefix, index_name = parsed
            grouped.setdefault(date_prefix, {})[index_name] = file_path

        for date_prefix, files in sorted(grouped.items()):
            if required.issubset(files.keys()):
                samples.append(
                    SampleItem(
                        field_name=root.name,
                        date_prefix=date_prefix,
                        files={key: files[key] for key in required},
                    )
                )

    if not samples:
        raise RuntimeError(
            "Не найдено ни одного полного набора изображений. "
            "Для каждой даты нужны: " + ", ".join(sorted(required))
        )

    return samples


def _load_grayscale(path: Path, size: Tuple[int, int]) -> np.ndarray:
    img = Image.open(path).convert("L")
    img = img.resize(size, Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return arr[None, :, :]  # 1 x H x W


def _load_rgb(path: Path, size: Tuple[int, int]) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    img = img.resize(size, Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.transpose(arr, (2, 0, 1))  # 3 x H x W


def load_input_tensor(files: Dict[str, Path], size: Tuple[int, int]) -> torch.Tensor:
    channels: List[np.ndarray] = []

    for index_name in INDEX_INPUTS:
        path = files[index_name]
        if index_name == "True_Color":
            channels.append(_load_rgb(path, size))
        else:
            channels.append(_load_grayscale(path, size))

    x = np.concatenate(channels, axis=0)  # 9 x H x W
    return torch.from_numpy(x).float()


def load_target_tensor(files: Dict[str, Path], size: Tuple[int, int]) -> torch.Tensor:
    y = _load_grayscale(files[TARGET_INDEX], size)  # 1 x H x W
    return torch.from_numpy(y).float()


class SentinelNdviDataset(Dataset):
    def __init__(
        self,
        samples: Sequence[SampleItem],
        image_size: Tuple[int, int] = (180, 120),
        augment: bool = False,
    ) -> None:
        self.samples = list(samples)
        self.image_size = image_size  # PIL ждёт (width, height)
        self.augment = augment

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        item = self.samples[idx]
        x = load_input_tensor(item.files, self.image_size)
        y = load_target_tensor(item.files, self.image_size)

        if self.augment:
            if torch.rand(1).item() < 0.5:
                x = torch.flip(x, dims=[2])
                y = torch.flip(y, dims=[2])
            if torch.rand(1).item() < 0.5:
                x = torch.flip(x, dims=[1])
                y = torch.flip(y, dims=[1])

            noise = torch.randn_like(x) * 0.01
            x = torch.clamp(x + noise, 0.0, 1.0)

        return x, y, item.date_prefix, item.field_name
