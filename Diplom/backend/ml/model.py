from __future__ import annotations

import torch
from torch import nn


class MultiScaleNDVICNN(nn.Module):
    """
    Упрощённая многомасштабная CNN для реконструкции NDVI-карты.
    Вход: 9 каналов: RGB True Color + 6 индексов.
    Выход: 1 канал NDVI-карты в диапазоне [0, 1].
    """

    def __init__(self, in_channels: int = 9) -> None:
        super().__init__()

        self.branch3 = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.branch5 = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
        )
        self.branch7 = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=7, padding=3),
            nn.ReLU(inplace=True),
        )

        self.decoder = nn.Sequential(
            nn.Conv2d(96, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 1, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x3 = self.branch3(x)
        x5 = self.branch5(x)
        x7 = self.branch7(x)
        features = torch.cat([x3, x5, x7], dim=1)
        return self.decoder(features)
