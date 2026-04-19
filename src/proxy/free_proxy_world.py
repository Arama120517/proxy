import json
import random
import re
import time
from urllib.parse import ParseResult, parse_qs, urlparse

from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet

from proxy.utils import (
    MAX_INDEX_NUM,
    RESULTS_DIR_PATH,
    OutBounds,
    create_outbound,
    requests_flaresolverr,
)


def get_href_param(tag: Tag | None, param_name) -> str | None:
    if not tag or not tag.has_attr("href") or not isinstance(tag["href"], str):
        return None
    parsed_url: ParseResult = urlparse(tag["href"])
    query_params: dict[str, list[str]] = parse_qs(parsed_url.query)
    return query_params.get(param_name, [None])[0]


results: OutBounds = []

index: int = 1
timeout: bool = False
while not timeout and index < MAX_INDEX_NUM:
    for row in BeautifulSoup(
        requests_flaresolverr(
            f"https://www.freeproxy.world?type=&anonymity=&country=&speed=600&port=&page={index}",
            str,
        ),
        "html.parser",
    ).find_all("tr"):
        cols: ResultSet[Tag] = row.find_all("td")

        if not cols or len(cols) < 8:
            continue

        total_minutes = 0
        for value, unit in re.findall(
            r"(\d+)\s*([dh]\.?|minutes)", cols[7].get_text(strip=True)
        ):
            val = int(value)
            if "d" in unit:
                total_minutes += val * 24 * 60
            elif "h" in unit:
                total_minutes += val * 60
            elif "minutes" in unit:
                total_minutes += val
        if total_minutes > 120:
            timeout = True
            break

        if get_href_param(cols[2].find("a"), "country") == "CN":
            continue

        port: str | None = get_href_param(cols[1].find("a"), "port")
        if not port or not port.isdigit():
            continue

        server: str = cols[0].get_text(strip=True)

        protocols: list[str] = []
        for protocol_tag in cols[5].find_all("a"):
            protocol: str | None = get_href_param(protocol_tag, "type")
            if protocol:
                protocols.append(protocol.upper())
        if not protocols:
            continue
        try:
            results.append(create_outbound(server, int(port), protocols))
        except ValueError:
            continue
    time.sleep(random.uniform(1, 3))
    index += 1

(RESULTS_DIR_PATH / "free_proxy_world.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
