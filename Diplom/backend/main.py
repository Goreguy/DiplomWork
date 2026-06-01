from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():

    return {
        "message": "Backend works"
    }


@app.post("/analyze")
def analyze(data: dict):

    points = data["points"]

    print(points)

    return {
        "status": "success",
        "points_count": len(points)
    }