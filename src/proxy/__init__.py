import json
from pathlib import Path
from typing import Any

from requests import Session
from ua_generator import generate

try:
    import dotenv

    dotenv.load_dotenv()
except (ModuleNotFoundError, IOError):
    pass

__all__ = ['OutBound', 'OutBounds', 'get_session', 'load_result', 'dump_result']

type OutBound = dict[str, Any]
type OutBounds = list[OutBound]


def get_session() -> Session:
    session = Session()
    session.headers.update({'User-Agent': generate().text})
    return session


def load_result() -> OutBounds:
    outbounds: OutBounds = []

    for result_dir in [f for f in Path('./results').iterdir() if f.is_dir()]:
        with (result_dir / 'result.json').open('r', encoding='utf-8') as f:
            outbounds += json.load(f)

    return outbounds


def dump_result(outbounds: OutBounds) -> None:
    results = []
    with Path('./result.json').open('w', encoding='utf-8') as f:
        for outbound in outbounds:
            if 'server' in outbound:
                results.append(outbound)
        json.dump(results, f, ensure_ascii=False)


# class BaseSource(ABC, Session):
#     logger: logging.Logger

#     def __init__(self):
#         super().__init__()

#         self.headers.update({'User-Agent': generate().text})
#         self.logger = logging.getLogger(self.__class__.__name__)

#     def main(self) -> NoReturn:
#         """运行程序"""

#         from sys import exit

#         from rich import print_json

#         try:
#             servers = self.get_outbounds()
#             print_json(data=servers, indent=4, ensure_ascii=False)
#         except Exception:
#             self.logger.exception('获取失败')

#         exit(0)

#     @abstractmethod
#     def get_outbounds(self) -> OutBounds: ...

#     @staticmethod
#     def extract_proxy_servers(config: dict) -> OutBounds:
#         return [o for o in config.get('outbounds', []) if o.get('server')]
