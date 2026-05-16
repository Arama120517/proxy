"""自动更新"""

from contextlib import suppress

from proxy.utils import OUTPUT_DIR, RESULTS_DIR

# 检测是否是开发环境
with suppress(Exception):
    import dotenv
    from dns.resolver import get_default_resolver

    dotenv.load_dotenv()
    get_default_resolver().nameservers: list[str] = [
        "114.114.114.114",
        "114.114.115.115",
    ]
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

__all__: list[str] = []
