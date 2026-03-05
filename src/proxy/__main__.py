import json
import logging
from ipaddress import ip_address
from pathlib import Path

from dns.resolver import NoAnswer, Resolver
from geoip2.database import Reader

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
with Reader('Country.mmdb') as geo_reader:
    resolver = Resolver()
    for source in SOURCES:
        try:
            for outbound in source.get_outbounds():
                type_servers = servers.setdefault(outbound['type'], [])
                # 防止重复
                if outbound['server'] in type_servers:
                    continue
                ip = outbound['server']

                # 设备无法使用anytls作为type
                if outbound['type'] == 'anytls':
                    continue

                try:
                    ip_address(ip)
                except ValueError:
                    try:
                        ip = str(resolver.resolve(ip, 'A')[0])
                    except (NoAnswer, Exception):
                        # 可能是IPv6地址
                        ip = str(resolver.resolve(ip, 'AAAA')[0])

                response = geo_reader.country(ip)

                country_code = response.country.iso_code
                if country_code == 'CN':
                    continue

                flag_emoji = country_code_to_flag_emoji(country_code)
                tag: str = f'{flag_emoji} | {response.country.iso_code} | [{outbound["type"]}]-{len(type_servers)}'
                outbound['tag'] = tag
                template['outbounds'][0]['outbounds'].append(tag)
                template['outbounds'][1]['outbounds'].append(tag)
                template['outbounds'].insert(-3, outbound)

                servers[outbound['type']].append(outbound['server'])
        except NoAnswer:  # 不可用
            continue
        except Exception:
            logging.exception('获取节点失败')
            continue

with open('./release_notes.md', 'w', encoding='utf-8') as f:
    f.write("""| 类型 | 节点数量 |
| ---- | -------- |
""")
    for tag, servers_list in servers.items():
        f.write(f'| {tag} | {len(servers_list)} |\n')

with open(CURRENT_DIR_PATH / 'result.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(template, indent=4, ensure_ascii=False))
