import json
import random
import time
from datetime import datetime

from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet

from proxy.utils import (
    MAX_INDEX_NUM,
    MAX_NO_VALID_INDEX_NUM,
    RESULTS_DIR_PATH,
    OutBounds,
    create_outbound,
    requests_flaresolverr,
)

results: OutBounds = []
now: datetime = datetime.now()

index: int = 1
no_any_valid_nodes_num: int = 0
while (
    no_any_valid_nodes_num <= MAX_NO_VALID_INDEX_NUM and index < MAX_INDEX_NUM
):  # 最多3次没有任何有效节点就停止
    outbounds_num: int = len(results)
    for row in BeautifulSoup(
        requests_flaresolverr(
            f"https://proxy.scdn.io/get_proxies.php?per_page=100&page={index}", dict
        )["table_html"],
        "html.parser",
    ).find_all("tr"):
        cols: ResultSet[Tag] = row.find_all("td")

        if not cols or len(cols) < 6:
            continue

        if int(cols[4].get_text(strip=True).replace("ms", "")) > 300:
            timeout = True
            break

        country: str = cols[3].get_text(strip=True)
        if country == "中国" or country == "中華人民共和國":
            continue

        port: str = cols[1].get_text(strip=True)
        if not port.isdigit():
            continue
        server: str = cols[0].get_text(strip=True)

        protocols: list[str] = [
            p.strip() for p in cols[2].get_text(strip=True).split("/") if p.strip()
        ]
        if not protocols:
            continue

        try:
            results.append(create_outbound(server, int(port), protocols))
        except ValueError:
            continue
    if len(results) == outbounds_num:
        no_any_valid_nodes_num += 1
    else:
        no_any_valid_nodes_num = 0

    time.sleep(random.uniform(1, 3))
    index += 1

(RESULTS_DIR_PATH / "proxy_scdn_io.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
