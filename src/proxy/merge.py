from json import loads

from yaml import safe_dump

from proxy.utils import CURRENT_DIR, RESULTS_DIR, OutBounds

results: OutBounds = []
for result_file in [
    f for f in RESULTS_DIR.iterdir() if f.is_file() and f.suffix == ".json"
]:
    results += loads(result_file.read_text(encoding="utf-8"))

for i, result in enumerate(results):
    result["name"] = f"proxy-{i}"


(CURRENT_DIR / "output" / "results.yaml").write_text(
    safe_dump({"proxies": results}, allow_unicode=True, sort_keys=False, indent=2),
    encoding="utf-8",
)
