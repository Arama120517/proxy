import json
import logging
from pathlib import Path

from rich.logging import RichHandler

from src import BaseSource
from src.free_clash_node import FreeClashNodeSource
from src.jegocloud import JegoCloudSource

logging.root.addHandler(RichHandler(rich_tracebacks=True))
logging.root.setLevel(logging.INFO)

MODULES: list[BaseSource] = [JegoCloudSource(), FreeClashNodeSource()]

CURRENT_DIR_PATH: Path = Path().cwd()
SRC_DIR_PATH: Path = CURRENT_DIR_PATH / 'src'


def main() -> None:
    with open(SRC_DIR_PATH / 'template.json', 'r', encoding='utf-8') as f:
        template: dict = json.loads(f.read())

    servers: list[str] = []
    for module in MODULES:
        for outbound in module.get_outbounds():
            # 防止重复
            if outbound['server'] in servers:
                continue

            tag: str = outbound['tag']
            template['outbounds'][0]['outbounds'].append(tag)
            template['outbounds'][1]['outbounds'].append(tag)
            template['outbounds'].insert(-3, outbound)

            servers.append(outbound['server'])

    with open(CURRENT_DIR_PATH / 'result.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(template, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
