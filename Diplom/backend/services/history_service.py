from __future__ import annotations

from datetime import datetime, timedelta

from services.ndvi_service import get_ndvi_for_period
from services.weather_service import get_precipitation


def generate_dates():
    """Формирует пять 7-дневных интервалов с шагом 14 дней."""
    dates = []
    current = datetime.now()

    for i in range(5):
        end_date = current - timedelta(days=i * 14)
        start_date = end_date - timedelta(days=7)
        dates.append((start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

    return dates


def get_ndvi_history(points):
    """
    Возвращает историю NDVI и осадков.

    Любая проблема с погодным API или Sentinel Hub теперь не роняет endpoint
    /history. Для проблемного интервала возвращается 0.0 и текст предупреждения.
    """
    history = []

    center_lat = sum(p.lat for p in points) / len(points)
    center_lon = sum(p.lon for p in points) / len(points)

    for start_date, end_date in generate_dates():
        warning_parts = []

        try:
            ndvi = float(get_ndvi_for_period(points, start_date, end_date))
        except Exception as exc:
            print(f"[history_service] Ошибка NDVI {start_date} - {end_date}: {exc}")
            ndvi = 0.0
            warning_parts.append("NDVI не получен")

        try:
            rainfall = float(get_precipitation(center_lat, center_lon, start_date, end_date))
        except Exception as exc:
            print(f"[history_service] Ошибка погоды {start_date} - {end_date}: {exc}")
            rainfall = 0.0
            warning_parts.append("осадки не получены")

        item = {
            "start_date": start_date,
            "end_date": end_date,
            "ndvi": ndvi,
            "rainfall": rainfall,
        }

        if warning_parts:
            item["warning"] = ", ".join(warning_parts)

        history.append(item)

    return history