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
import matplotlib.pyplot as plt


config = SHConfig()

config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET


def generate_ndvi_heatmap(
    points,
    start_date,
    end_date
):

    min_lon = min(p.lon for p in points)
    max_lon = max(p.lon for p in points)

    min_lat = min(p.lat for p in points)
    max_lat = max(p.lat for p in points)

    bbox = BBox(
        bbox=[min_lon, min_lat, max_lon, max_lat],
        crs=CRS.WGS84
    )

    width = max_lon - min_lon
    height = max_lat - min_lat

    ratio = width / height

    base = 512

    if ratio > 1:
        size = (base, int(base / ratio))
    else:
        size = (int(base * ratio), base)

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
        size=size,
        config=config,
    )

    data = request.get_data()[0]

    red = data[:, :, 0]
    nir = data[:, :, 1]

    ndvi = (nir - red) / (nir + red + 1e-6)

    plt.figure(figsize=(8, 6))

    plt.imshow(
        ndvi,
        cmap="RdYlGn",
        vmin=-1,
        vmax=1
    )

    plt.colorbar(label="NDVI")

    plt.axis("off")

    plt.savefig(
        "static/ndvi_heatmap.png",
        bbox_inches="tight"
    )

    plt.close()

    return "/static/ndvi_heatmap.png"