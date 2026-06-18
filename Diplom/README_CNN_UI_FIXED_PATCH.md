# Патч CNN + исправление падения `/history`

Этот патч добавляет CNN-модуль в интерфейс и исправляет ошибку:

```text
KeyError: 'daily'
```

Ошибка появлялась в `backend/services/weather_service.py`, потому что Open-Meteo иногда возвращает ответ без поля `daily`: например, если период слишком свежий, API временно недоступен или пришла ошибка. Старая версия кода напрямую обращалась к `data["daily"]["precipitation_sum"]`, из-за чего весь FastAPI endpoint `/history` падал.

## Что исправлено

### Backend

- `backend/services/weather_service.py` — безопасная обработка ответа Open-Meteo. Если `daily` отсутствует, возвращается `0.0`, backend не падает.
- `backend/services/history_service.py` — история NDVI теперь не падает из-за одного проблемного периода.
- `backend/services/ndvi_service.py` — добавлена более аккуратная SCL-маска облаков, теней, снега и пикселей без данных.
- `backend/services/heatmap_service.py` — NDVI-карта строится с фильтрацией облаков; если валидных пикселей нет, создаётся заглушка вместо падения.
- `backend/services/rgb_service.py` — RGB-снимок получает `dataMask`; если Sentinel Hub не вернул снимок, создаётся заглушка.
- `backend/services/ml_service.py` — сервис CNN-модуля.
- `backend/ml/` — датасет, модель, обучение и прогноз CNN.
- `backend/main.py` — добавлен endpoint `GET /ml/predict-demo`, остальные endpoint обёрнуты в безопасную обработку ошибок.

### Frontend

- `lib/pages/main_page.dart` — после основного анализа вызывается CNN endpoint.
- `lib/pages/analysis_result_page.dart` — добавлен блок «CNN-модуль реконструкции NDVI».

## Как вставить

1. Сделай резервную копию проекта.
2. Распакуй архив в корень проекта с заменой файлов.
3. Из папки `backend` установи ML-зависимости:

```bash
pip install torch numpy pillow matplotlib
```

## Как обучить CNN

Из папки `backend`:

```bash
python -m ml.train --data-dirs "D:/dataset/field_1" "D:/dataset/field_2" --epochs 100 --batch-size 8
```

После обучения должен появиться файл:

```text
backend/ml_runs/ndvi_cnn/ndvi_cnn_model.pth
```

## Как указать dataset для интерфейса

PowerShell:

```powershell
$env:CNN_DATASET_DIRS="D:\dataset\field_1;D:\dataset\field_2"
```

Либо добавь в `backend/config.py`:

```python
DATASET_DIRS = [
    r"D:\dataset\field_1",
    r"D:\dataset\field_2",
]
```

## Проверка

Запусти backend из папки `backend`:

```bash
uvicorn main:app --reload
```

Проверь:

```text
http://127.0.0.1:8000/ml/predict-demo
```

Если модель обучена и пути к датасету указаны, вернётся JSON с `image_url`, `mean_predicted_ndvi`, `mse`, `mae`, `r2`.

## Важно

CNN-блок сейчас демонстрационный: он выводит реконструкцию NDVI по примеру из подготовленного датасета. Основной анализ выбранного на карте полигона продолжает работать через Sentinel Hub: `/analyze`, `/heatmap`, `/rgb`, `/history`.
