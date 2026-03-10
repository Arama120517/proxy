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

    for result_file in [
        f for f in Path('./results').iterdir() if f.is_file() and f.suffix == '.json'
    ]:
        with result_file.open('r', encoding='utf-8') as f:
            outbounds += json.load(f)

    return outbounds


def dump_result(outbounds: OutBounds) -> None:
    results = []
    for outbound in outbounds:
        if 'server' in outbound:
            results.append(outbound)
    print(json.dumps(results, ensure_ascii=False))
