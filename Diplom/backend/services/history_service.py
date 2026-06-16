from datetime import datetime, timedelta
from services.ndvi_service import get_ndvi_for_period

def generate_dates():

    dates = []

    current = datetime.now()

    for i in range(5):

        end_date = current - timedelta(days=i * 14)

        start_date = end_date - timedelta(days=7)

        dates.append(
            (
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
        )

    return dates

def get_ndvi_history(points):

    history = []

    for start_date, end_date in generate_dates():

        ndvi = get_ndvi_for_period(
            points,
            start_date,
            end_date
        )

        history.append({
    "start_date": start_date,
    "end_date": end_date,
    "ndvi": ndvi
})

    return history
