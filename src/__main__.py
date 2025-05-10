import json
import logging
from pathlib import Path

from rich.logging import RichHandler

from src import ProxyServerGenerator
from src.freeclassnode import FreeClassNode
from src.jegocloud import JegoCloud

logging.root.addHandler(RichHandler(rich_tracebacks=True))
logging.root.setLevel(logging.INFO)

logger: logging.Logger = logging.getLogger(__name__)

modules: list[ProxyServerGenerator] = [JegoCloud(), FreeClassNode()]

CURRENT_DIR_PATH: Path = Path().cwd()
SRC_DIR_PATH: Path = CURRENT_DIR_PATH / 'src'


def main() -> None:
    with open(SRC_DIR_PATH / 'template.json', 'r', encoding='utf-8') as f:
        template: dict = json.loads(f.read())

    for module in modules:
        for outbound in module.generate():
            tag: str = outbound['tag']
            template['outbounds'][0]['outbounds'].append(tag)
            template['outbounds'][1]['outbounds'].append(tag)
            template['outbounds'].insert(-3, outbound)

    with open(CURRENT_DIR_PATH / 'result.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(template, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
