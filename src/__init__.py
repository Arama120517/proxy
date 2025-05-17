import logging
from abc import ABC, abstractmethod

from requests import Session
from ua_generator import generate


class ProxyServerGenerator(ABC, Session):
    logger: logging.Logger

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.headers.update({'User-Agent': generate().text})

    @abstractmethod
    def generate(self) -> list[dict]: ...
