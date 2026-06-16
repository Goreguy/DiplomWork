from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
)

from datetime import datetime, timedelta
from config import CLIENT_ID, CLIENT_SECRET

import numpy as np


config = SHConfig()

config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET


def analyze_ndvi(points):

    end_date = datetime.now()

    start_date = end_date - timedelta(days=7)

    mean_ndvi = get_ndvi_for_period(
        points,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    if mean_ndvi < 0.2:
        status = "Плохое состояние"
    elif mean_ndvi < 0.5:
        status = "Среднее состояние"
    else:
        status = "Хорошее состояние"

    return {
        "mean_ndvi": mean_ndvi,
        "status": status
    }

def get_ndvi_for_period(points, start_date, end_date):
    # bbox из полигона

    min_lon = min(p.lon for p in points)
    max_lon = max(p.lon for p in points)

    min_lat = min(p.lat for p in points)
    max_lat = max(p.lat for p in points)

    bbox = BBox(
        bbox=[min_lon, min_lat, max_lon, max_lat],
        crs=CRS.WGS84
    )

    # Sentinel request

    request = SentinelHubRequest(

        evalscript = """
//VERSION=3

        function setup() {
          return {
            input: ["B04", "B08"],
            output: { bands: 2 }
          };
        }

        function evaluatePixel(sample) {
          return [
            sample.B04, // Red
            sample.B08  // NIR
          ];
        }
        """,

        input_data=[
    SentinelHubRequest.input_data(
        data_collection=DataCollection.SENTINEL2_L2A,
        time_interval=(start_date, end_date)
    )
],

        responses=[
            SentinelHubRequest.output_response(
                "default",
                MimeType.TIFF
            )
        ],

        bbox=bbox,

        size=(256, 256),

        config=config,
    )

    data = request.get_data()[0]

    red = data[:, :, 0]
    nir = data[:, :, 1]


    denom = nir + red

    ndvi = np.where(
        denom == 0,
        0,
        (nir - red) / denom
    )

    mean_ndvi = float(np.mean(ndvi))

    # классификация

    if mean_ndvi < 0.2:
        status = "Плохое состояние"

    elif mean_ndvi < 0.5:
        status = "Среднее состояние"

    else:
        status = "Хорошее состояние"

    return mean_ndvi

