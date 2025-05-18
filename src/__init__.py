import logging
import re
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup
from requests import Response, Session
from ua_generator import generate


class BaseSource(ABC, Session):
    logger: logging.Logger

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers.update({'User-Agent': generate().text})

    @abstractmethod
    def generate(self) -> list[dict]: ...

    @staticmethod
    def from_full_config_get_proxy_servers(config: dict) -> list[dict]:
        servers: list[dict] = []
        for outbound in config['outbounds']:
            if 'server' not in outbound:
                continue
            servers.append(outbound)
        return servers

    def from_clash_source_get_proxy_servers(self, url: str) -> list[dict]:
        response = self.get(f'https://clash2sfa.xmdhs.com/sub?sub={url}')
        response.raise_for_status()
        return self.from_full_config_get_proxy_servers(response.json())

    def from_website_get_source_urls(self, url: str, file_suffix: str = 'json') -> list[str]:
        response: Response = self.get(url)
        response.raise_for_status()

        be_found_url = re.findall(rf'https?://[^\s<>"\']+?\.{file_suffix}', response.text)
        if not be_found_url:
            raise RuntimeError('正则表达式没有匹配到任何链接')

        return be_found_url
