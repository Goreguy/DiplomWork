from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from ml.dataset import INDEX_INPUTS, SentinelNdviDataset, discover_samples
from ml.model import MultiScaleNDVICNN


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def r2_score_torch(y_true: torch.Tensor, y_pred: torch.Tensor) -> float:
    y_true = y_true.reshape(-1)
    y_pred = y_pred.reshape(-1)
    ss_res = torch.sum((y_true - y_pred) ** 2)
    ss_tot = torch.sum((y_true - torch.mean(y_true)) ** 2)
    if ss_tot.item() == 0:
        return 0.0
    return float((1 - ss_res / ss_tot).item())


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> Dict[str, float]:
    model.eval()
    mse_values = []
    mae_values = []
    all_true = []
    all_pred = []

    for x, y, _, _ in loader:
        x = x.to(device)
        y = y.to(device)
        pred = model(x)
        mse_values.append(torch.mean((pred - y) ** 2).item())
        mae_values.append(torch.mean(torch.abs(pred - y)).item())
        all_true.append(y.detach().cpu())
        all_pred.append(pred.detach().cpu())

    y_true = torch.cat(all_true, dim=0)
    y_pred = torch.cat(all_pred, dim=0)

    return {
        "mse": float(np.mean(mse_values)),
        "mae": float(np.mean(mae_values)),
        "r2": r2_score_torch(y_true, y_pred),
    }


@torch.no_grad()
def save_prediction_example(model: nn.Module, dataset: SentinelNdviDataset, device: torch.device, out_path: Path) -> None:
    model.eval()
    x, y, date_prefix, field_name = dataset[0]
    pred = model(x.unsqueeze(0).to(device)).squeeze().cpu().numpy()
    true = y.squeeze().numpy()
    error = np.abs(true - pred)

    fig = plt.figure(figsize=(12, 4))

    ax1 = fig.add_subplot(1, 3, 1)
    ax1.imshow(true, vmin=0, vmax=1)
    ax1.set_title("Истинная NDVI-карта")
    ax1.axis("off")

    ax2 = fig.add_subplot(1, 3, 2)
    ax2.imshow(pred, vmin=0, vmax=1)
    ax2.set_title("Прогноз CNN")
    ax2.axis("off")

    ax3 = fig.add_subplot(1, 3, 3)
    ax3.imshow(error, vmin=0, vmax=max(0.1, float(error.max())))
    ax3.set_title("Карта ошибки")
    ax3.axis("off")

    fig.suptitle(f"{field_name}: {date_prefix}")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Обучение CNN для реконструкции NDVI")
    parser.add_argument("--data-dirs", nargs="+", required=True, help="Папки с изображениями полей")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output-dir", default="ml_runs/ndvi_cnn")
    parser.add_argument("--width", type=int, default=180)
    parser.add_argument("--height", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = discover_samples(args.data_dirs)
    random.shuffle(samples)

    split_idx = max(1, int(len(samples) * 0.8))
    train_samples = samples[:split_idx]
    test_samples = samples[split_idx:]

    if not test_samples:
        raise RuntimeError("Слишком мало данных для тестовой выборки")

    train_ds = SentinelNdviDataset(train_samples, image_size=(args.width, args.height), augment=True)
    test_ds = SentinelNdviDataset(test_samples, image_size=(args.width, args.height), augment=False)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiScaleNDVICNN(in_channels=9).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()

    best_mse = float("inf")
    history = []

    print(f"Найдено полных наборов: {len(samples)}")
    print(f"Обучение: {len(train_samples)}, тест: {len(test_samples)}")
    print(f"Устройство: {device}")
    print(f"Входные признаки: {', '.join(INDEX_INPUTS)}")
    print("Цель: NDVI")

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses = []

        for x, y, _, _ in train_loader:
            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad()
            pred = model(x)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())

        metrics = evaluate(model, test_loader, device)
        train_loss = float(np.mean(train_losses))
        row = {"epoch": epoch, "train_mse": train_loss, **metrics}
        history.append(row)

        print(
            f"Epoch {epoch:03d}/{args.epochs} | "
            f"train MSE={train_loss:.6f} | "
            f"test MSE={metrics['mse']:.6f} | "
            f"MAE={metrics['mae']:.6f} | R2={metrics['r2']:.4f}"
        )

        if metrics["mse"] < best_mse:
            best_mse = metrics["mse"]
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "in_channels": 9,
                    "image_size": [args.width, args.height],
                    "input_indexes": INDEX_INPUTS,
                    "target": "NDVI",
                    "metrics": metrics,
                },
                output_dir / "ndvi_cnn_model.pth",
            )

    with open(output_dir / "training_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    best_checkpoint = torch.load(output_dir / "ndvi_cnn_model.pth", map_location=device)
    model.load_state_dict(best_checkpoint["model_state_dict"])

    final_metrics = evaluate(model, test_loader, device)
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_metrics, f, ensure_ascii=False, indent=2)

    save_prediction_example(model, test_ds, device, output_dir / "prediction_example.png")

    print("\nГотово.")
    print(f"Модель: {output_dir / 'ndvi_cnn_model.pth'}")
    print(f"Метрики: {output_dir / 'metrics.json'}")
    print(f"Пример прогноза: {output_dir / 'prediction_example.png'}")


if __name__ == "__main__":
    main()
