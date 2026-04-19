import json

import yaml
from fastapi import FastAPI, Response
from uvicorn import run

from proxy.utils import RESULTS_DIR_PATH, OutBounds

results: OutBounds = []
for result_file in [
    f for f in RESULTS_DIR_PATH.iterdir() if f.is_file() and f.suffix == ".json"
]:
    results += json.loads(result_file.read_text(encoding="utf-8"))

for i, result in enumerate(results):
    result["name"] = f"proxy-{i}"

result: str = yaml.safe_dump(
    {"proxies": results}, allow_unicode=True, sort_keys=False, indent=2
)

app = FastAPI()


@app.get("/")
def get_proxies():
    return Response(content=result, media_type="application/x-yaml")


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


run(app, host="127.0.0.1", port=3000)
