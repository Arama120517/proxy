import json
import logging
from pathlib import Path
from socket import gethostbyname

import requests

from proxy import BaseSource
from proxy.free_clash_node import FreeClashNodeSource
from proxy.jegocloud import JegoCloudSource

SOURCES: list[BaseSource] = [JegoCloudSource(), FreeClashNodeSource()]

CURRENT_DIR_PATH: Path = Path().cwd()
SRC_DIR_PATH: Path = CURRENT_DIR_PATH / 'src'


def country_code_to_flag_emoji(code: str) -> str:
    """'US' -> '🇺🇸'"""
    if not code or len(code) != 2:
        return '🌐'
    try:
        return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in code.upper())
    except Exception:
        return '❓'


with open(SRC_DIR_PATH / 'template.json', 'r', encoding='utf-8') as f:
    template: dict = json.loads(f.read())

servers: dict[str, list[str]] = {}
for source in SOURCES:
    try:
        for outbound in source.get_outbounds():
            type_servers = servers.setdefault(outbound['type'], [])
            # 防止重复
            if outbound['server'] in type_servers:
                continue
            ip = gethostbyname(outbound['server'])

            response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=6)
            response.raise_for_status()

            data = response.json()
            country_code = data.get('country', '').strip()
            country_name = data.get('country_name') or data.get('region') or '未知'
            flag_emoji = country_code_to_flag_emoji(country_code)

            tag: str = f'{flag_emoji} | {country_name} | [{outbound["type"]}]-{len(type_servers)}'
            outbound['tag'] = tag
            template['outbounds'][0]['outbounds'].append(tag)
            template['outbounds'][1]['outbounds'].append(tag)
            template['outbounds'].insert(-3, outbound)

            servers[outbound['type']].append(outbound['server'])
            logging.info(f'添加节点: {tag} - {outbound["server"]}:{outbound["server_port"]}')
    except Exception:
        logging.exception(f'从 {source.__class__.__name__} 获取节点失败')
        continue

with open('./release_notes.md', 'w', encoding='utf-8') as f:
    f.write(f"""## 结果

- **节点总数**: {len(template['outbounds']) - 5}

| 类型 | 节点数量 |
| ---- | -------- |
""")
    for tag, servers_list in servers.items():
        f.write(f'| {tag} | {len(servers_list)} |\n')

with open(CURRENT_DIR_PATH / 'result.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(template, indent=4, ensure_ascii=False))
