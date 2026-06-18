from __future__ import annotations

from typing import Any

import requests


def _safe_sum(values: Any) -> float:
    if not isinstance(values, list):
        return 0.0

    total = 0.0
    for value in values:
        if value is None:
            continue
        try:
            total += float(value)
        except (TypeError, ValueError):
            continue
    return total


def get_precipitation(lat, lon, start_date, end_date) -> float:
    """
    Возвращает сумму осадков за период по Open-Meteo Archive API.

    В старой версии код напрямую обращался к data["daily"]. Если Open-Meteo
    возвращал ошибку, пустой ответ, слишком свежий период или временный сбой,
    backend падал с KeyError: 'daily'. Теперь сервис не роняет приложение:
    при проблемах возвращается 0.0, а ошибка печатается в консоль.
    """

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
        "&daily=precipitation_sum"
        "&timezone=auto"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"[weather_service] Не удалось получить погоду: {exc}")
        return 0.0

    daily = data.get("daily")
    if not isinstance(daily, dict):
        reason = data.get("reason") or data.get("error") or "поле daily отсутствует"
        print(f"[weather_service] Open-Meteo вернул ответ без daily: {reason}")
        return 0.0

    rainfall = _safe_sum(daily.get("precipitation_sum"))
    return float(rainfall)
