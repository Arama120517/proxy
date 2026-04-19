import json
import random
import re
import time

from bs4 import BeautifulSoup, Tag
from bs4.element import AttributeValueList, ResultSet

from proxy.utils import (
    MAX_INDEX_NUM,
    MAX_NO_VALID_INDEX_NUM,
    RESULTS_DIR_PATH,
    OutBounds,
    create_outbound,
    requests_flaresolverr,
)


def extract_auth_field(td_element: Tag) -> str:
    img: Tag | None = td_element.find("img", class_="js_openeyes")
    if img and img.get("data-text") and isinstance(img["data-text"], str):
        value: str = img["data-text"]
        return "" if value.lower() in ("no need", "none", "null") else value
    for attr in ["data-value", "data-auth", "title"]:
        attr_value: str | AttributeValueList | None = td_element.get(attr)
        if attr_value and isinstance(attr_value, str):
            return attr_value.strip()
    text: str = td_element.get_text(strip=True)
    if text and text != "****":
        return text
    return ""


results: OutBounds = []

index: int = 1
no_any_valid_nodes_num: int = 0
while (
    no_any_valid_nodes_num <= MAX_NO_VALID_INDEX_NUM and index < MAX_INDEX_NUM
):  # 最多3次没有任何有效节点就停止
    outbounds_num: int = len(results)
    for row in BeautifulSoup(
        requests_flaresolverr(
            f"https://www.freevpnnode.com/free-proxy?page={index}",
            str,
        ),
        "html.parser",
    ).find_all("tr"):
        cols: ResultSet[Tag] = row.find_all("td")

        if len(cols) < 12:
            continue

        country_tag: Tag | None = cols[4].find("a")
        if not country_tag or country_tag.get_text(strip=True) == "CN":
            continue

        time_str: re.Match[str] | None = re.match(
            r"(\d+)\s*(sec|s|min|m|hour|h|hr|day|d)", cols[11].get_text(strip=True)
        )
        if not time_str:
            continue

        value = int(time_str.group(1))
        unit: str = time_str.group(2)

        multiplier: int = {
            "sec": 0,
            "s": 0,
            "min": 1,
            "m": 1,
            "hour": 60,
            "h": 60,
            "hr": 60,
            "day": 1440,
            "d": 1440,
        }.get(unit, 114514)  # 大于天的单位没有意义

        if value * multiplier > 120:
            continue

        latency_match: re.Match[str] | None = re.search(
            r"(\d+)", cols[10].get_text(strip=True)
        )
        latency: int | None = int(latency_match.group(1)) if latency_match else None
        if latency is None or latency > 300:
            continue

        port: str | None = cols[1].get_text(strip=True)
        if not port or not port.isdigit():
            continue

        server: str = cols[0].get_text(strip=True)

        protocols: list[str] = [cols[5].get_text(strip=True).upper()]

        username: str = extract_auth_field(cols[2])
        password: str = extract_auth_field(cols[3])

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

(RESULTS_DIR_PATH / "freevpnnode_com.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
