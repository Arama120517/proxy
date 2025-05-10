import logging
from abc import ABC, abstractmethod


class ProxyServerGenerator(ABC):
    logger: logging.Logger

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def generate(self) -> list[dict]: ...
