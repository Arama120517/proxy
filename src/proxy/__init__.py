"""自动更新"""

from proxy.utils import RESULTS_DIR_PATH

# 检测是否是开发环境
try:
    import dotenv
    from dns.resolver import get_default_resolver

    dotenv.load_dotenv()
    get_default_resolver().nameservers = ["114.114.114.114", "114.114.115.115"]
except OSError, ModuleNotFoundError:
    pass

RESULTS_DIR_PATH.mkdir(parents=True, exist_ok=True)
