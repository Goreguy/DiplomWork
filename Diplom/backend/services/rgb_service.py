from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
)

from config import CLIENT_ID, CLIENT_SECRET

from PIL import Image
import numpy as np


config = SHConfig()

config.sh_client_id = CLIENT_ID
config.sh_client_secret = CLIENT_SECRET


def generate_rgb_image(
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
    input: ["B04", "B03", "B02"],
    output: { bands: 3 }
  };
}

function evaluatePixel(s) {
  return [
    s.B04, // Red
    s.B03, // Green
    s.B02  // Blue
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
                MimeType.PNG
            )
        ],

        bbox=bbox,
        size=size,
        config=config,
    )

    data = request.get_data()[0]

    rgb = data

    p2 = np.percentile(rgb, 2)
    p98 = np.percentile(rgb, 98)

    rgb = np.clip(rgb, p2, p98)
    rgb = (rgb - p2) / (p98 - p2 + 1e-6)
    rgb = (rgb * 255).astype(np.uint8)

    Image.fromarray(rgb).save(
        "static/rgb.png"
    )

    return "/static/rgb.png"