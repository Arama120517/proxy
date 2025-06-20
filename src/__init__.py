import logging
from abc import ABC, abstractmethod
from typing import Any, NoReturn

from requests import Session
from rich.logging import RichHandler
from ua_generator import generate

# 测试用
try:
    import dotenv

    dotenv.load_dotenv()
except (ModuleNotFoundError, IOError):
    pass

OutBounds = list[dict[str, Any]]


class BaseSource(ABC, Session):
    logger: logging.Logger

    def __init__(self):
        super().__init__()

        self.headers.update({'User-Agent': generate().text})

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.level = logging.INFO
        self.logger.handlers = [RichHandler(rich_tracebacks=True)]

    def main(self) -> NoReturn:
        """运行程序"""

        from sys import exit

        from rich import print_json

        try:
            servers = self.get_outbounds()
            print_json(data=servers, indent=4, ensure_ascii=False)
        except Exception:
            self.logger.exception('获取失败')

        exit(0)

    @abstractmethod
    def get_outbounds(self) -> OutBounds: ...

    @staticmethod
    def extract_proxy_servers(config: dict) -> OutBounds:
        servers: OutBounds = []
        for outbound in config['outbounds']:
            if 'server' not in outbound:
                continue
            servers.append(outbound)
        return servers
