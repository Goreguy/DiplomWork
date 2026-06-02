from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
)

from config import CLIENT_ID, CLIENT_SECRET

import numpy as np


config = SHConfig()

config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET


def analyze_ndvi(points):

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

        evalscript="""
        //VERSION=3

        function setup() {
          return {
            input: ["B04", "B08"],
            output: {
              bands: 2,
              sampleType: "FLOAT32"
            }
          };
        }

        function evaluatePixel(sample) {
          return [
            sample.B04,
            sample.B08
          ];
        }
        """,

        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
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

    ndvi = (nir - red) / (nir + red + 1e-6)

    mean_ndvi = float(np.mean(ndvi))

    # классификация

    if mean_ndvi < 0.2:
        status = "Плохое состояние"

    elif mean_ndvi < 0.5:
        status = "Среднее состояние"

    else:
        status = "Хорошее состояние"

    return {
        "mean_ndvi": mean_ndvi,
        "status": status,
    }