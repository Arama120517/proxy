import json
import os
import re

from dns.rdatatype import TXT
from dns.resolver import resolve

from proxy.utils import RESULTS_DIR_PATH, create_outbound, requests_flaresolverr

# api_url: str = (
#     requests.get(
#         "https://doh.pub/resolve",
#         params={"name": "v3.jego.club", "type": "TXT"},
#         timeout=60,
#     )
#     .json()["Answer"][0]["data"]
#     .strip('"')
#     + "/chrome"
# )
api_url: str = resolve("v3.jego.club", TXT)[0].to_text().strip('"') + "/chrome"


# 登录
token: str = requests_flaresolverr(
    f"{api_url}/options/login",
    dict,
    method="POST",
    post_data=f"username={os.environ['JEGO_CLOUD_USERNAME']}&password={os.environ['JEGO_CLOUD_PASSWORD']}",
)["session"]["token"]

# 获取节点ip和端口
data: set[dict] = set(
    re.findall(
        r"HTTPS\s+(?P<host>[\w.-]+\.[a-zA-Z]{2,}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<port>\d+)",
        requests_flaresolverr(f"{api_url}/popup?token={token}", dict)["session"][
            "proxy_settings"
        ]["value"]["pacScript"]["data"],
    )
)
if not data:
    raise ValueError("No proxy data found")

(RESULTS_DIR_PATH / "jego_cloud.json").write_text(
    json.dumps(
        [create_outbound(server, int(port), ["HTTPS"]) for server, port in data],
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
