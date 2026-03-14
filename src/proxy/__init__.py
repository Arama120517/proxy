import json
from pathlib import Path
from typing import Any

from requests import Session
from ua_generator import generate

try:
    import dotenv

    dotenv.load_dotenv()
except ModuleNotFoundError, IOError:
    pass

__all__ = ['OutBound', 'get_session']

type OutBound = dict[str, Any]


def get_session() -> Session:
    session = Session()
    session.headers.update({'User-Agent': generate().text})
    return session
