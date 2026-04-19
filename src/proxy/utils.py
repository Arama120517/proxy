import json
from ipaddress import ip_address
from pathlib import Path
from typing import Any, Literal, overload

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import ConnectionError, Response

__all__: list[str] = [
    "CURRENT_DIR_PATH",
    "MAX_INDEX_NUM",
    "MAX_NO_VALID_INDEX_NUM",
    "RESULTS_DIR_PATH",
    "OutBound",
    "OutBounds",
    "create_outbound",
    "requests_flaresolverr",
]

# 定义常量
MAX_INDEX_NUM = 50
MAX_NO_VALID_INDEX_NUM = 3

# 定义路径
CURRENT_DIR_PATH: Path = Path.cwd()
RESULTS_DIR_PATH: Path = CURRENT_DIR_PATH / "results"

type OutBound = dict[str, Any]
type OutBounds = list[OutBound]


@overload
def requests_flaresolverr(
    url: str,
    data_type: type[str],
    method: Literal["GET", "POST"] = "GET",
    post_data: str | None = None,
) -> str: ...


@overload
def requests_flaresolverr(
    url: str,
    data_type: type[dict],
    method: Literal["GET", "POST"] = "GET",
    post_data: str | None = None,
) -> dict: ...


def requests_flaresolverr(
    url: str,
    data_type: type[str | dict],
    method: Literal["GET", "POST"] = "GET",
    post_data: str | None = None,
) -> str | dict:
    data: dict[str, str | bool] = {
        "cmd": f"request.{method.lower()}",
        "url": url,
        "disableMedia": True,
    }
    if method == "POST" and post_data:
        data["postData"] = post_data

    try:
        response: Response = requests.post(
            "http://localhost:8191/v1",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        response_json: Any = response.json()["solution"]
        response.status_code: int = response_json["status"]
    except ConnectionError:
        response: Response = requests.post(  # 开发者环境可以不开flaresolverr
            url,
            timeout=120,
            data=post_data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        )
        response_json: Any = response.json()
    response.raise_for_status()

    data: Any = response_json["response"]
    try:
        tag: Tag | None = BeautifulSoup(data, "html.parser").find("pre")
        if "</pre>" in data and tag:
            return json.loads(tag.get_text())
    except ValueError, TypeError:
        pass
    if not isinstance(data, data_type):
        raise ValueError
    return response_json["response"]


def create_outbound(
    server: str,
    port: int,
    protocols: list[str],
    username: str = "",
    password: str = "",
) -> OutBound:
    result: OutBound = {
        "server": server,
        "port": int(port),
        "skip-cert-verify": True,
    }

    if "SOCKS5" in protocols:
        result["type"] = "socks5"
        result["udp"] = True
    elif "HTTPS" in protocols:
        result["type"] = "http"
        result["tls"] = True
        try:
            ip_address(server)
        except ValueError:
            result["sni"] = server
    elif "HTTP" in protocols:
        result["type"] = "http"
    else:
        raise ValueError("Unsupported protocol")

    if username and password:
        result["username"] = username
        result["password"] = password
    return result
