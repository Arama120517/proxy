import json
import os
from dataclasses import dataclass
from pathlib import Path

from src import BaseSource
from src.free_clash_node import FreeClashNodeSource
from src.jegocloud import JegoCloudSource

SOURCES: list[BaseSource] = [JegoCloudSource(), FreeClashNodeSource()]

CURRENT_DIR_PATH: Path = Path().cwd()
SRC_DIR_PATH: Path = CURRENT_DIR_PATH / 'src'


@dataclass
class Status:
    success: bool
    tag_count: int


def main() -> None:
    with open(SRC_DIR_PATH / 'template.json', 'r', encoding='utf-8') as f:
        template: dict = json.loads(f.read())

    servers: list[str] = []
    status: dict[str, Status] = {}
    for source in SOURCES:
        name = source.__class__.__name__
        status[name] = Status(False, 0)
        try:
            for outbound in source.get_outbounds():
                # 防止重复
                if outbound['server'] in servers:
                    continue

                tag: str = outbound['tag']
                template['outbounds'][0]['outbounds'].append(tag)
                template['outbounds'][1]['outbounds'].append(tag)
                template['outbounds'].insert(-3, outbound)

                servers.append(outbound['server'])

                status[name].tag_count += 1
            status[name].success = True
        except Exception:
            continue

    with open(os.environ.get('GITHUB_STEP_SUMMARY'), 'w', encoding='utf-8') as f:
        f.write(f"""## 结果

- **节点总数**: {len(template['outbounds']) - 5}

| 名称 | 状态 | 节点数量 |
| ---- | ---- | -------- |
""")
        for name, stat in status.items():
            f.write(f'| {name} | {"✅" if stat.success else "❌"} | {stat.tag_count} |\n')

    with open(CURRENT_DIR_PATH / 'result.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(template, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
