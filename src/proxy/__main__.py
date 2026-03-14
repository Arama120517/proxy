import csv
import json
import os
import socket
from ipaddress import ip_address
from pathlib import Path

from dns.resolver import NoAnswer, Resolver
from geoip2.database import Reader
from geoip2.errors import AddressNotFoundError
from geoip2.records import Country

from proxy import OutBound, get_session

with open('./src/template.json', 'r', encoding='utf-8') as f:
    template: dict = json.loads(f.read())

country_outbounds: dict[tuple[str, str], list[OutBound]] = {}
seen_keys: set[str] = set()

outbounds: list[OutBound] = []
for result_file in [f for f in Path('./results').iterdir() if f.is_file() and f.suffix == '.json']:
    with result_file.open('r', encoding='utf-8') as f:
        outbounds += json.load(f)

# 筛选可用的节点并按照国家分类
with Reader('db.mmdb') as geo_reader:
    resolver = Resolver()
    for outbound in outbounds:
        try:
            if 'tag' in outbound:
                outbound.pop('tag')

            dedup_key: str = json.dumps(outbound, sort_keys=True, ensure_ascii=False)
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            if outbound['type'] == 'anytls':
                continue
            ip: str = outbound['server']

            try:
                ip_address(address=ip)
            except ValueError:
                try:
                    ip: str = socket.gethostbyname(ip)
                except socket.gaierror:
                    continue

            need_ipinfo: bool = False

            try:
                country: Country = geo_reader.country(ip).country
                result_key: tuple[str, str] = (
                    country.iso_code or '未知',
                    country.names.get('zh-CN', '未知'),
                )
            except AddressNotFoundError:  # 数据库里没有
                result: dict = (
                    get_session()
                    .get(f'https://api.ipinfo.io/lite/{ip}?token={os.environ["IPINFO_TOKEN"]}')
                    .json()
                )
                if not result['country'] or not isinstance(result['country'], str):
                    continue
                iso_code: str = result['country']
                with open('./locales.csv', 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['country_iso_code'] != iso_code:
                            continue
                        result_key: tuple[str, str] = (
                            iso_code,
                            row['country_name'] or '未知',
                        )
                        break

            if '未知' in result_key:
                continue

            if country.iso_code == 'CN':
                continue

            if country.iso_code == 'TW':
                result_key: tuple[str, str] = 'CN', '中国台湾'

            if result_key not in country_outbounds:
                country_outbounds[result_key] = []  # ty:ignore[invalid-assignment]
            country_outbounds[result_key].append(outbound)  # ty:ignore[invalid-argument-type]
        except NoAnswer:  # 不可用
            continue

# 添加到模板
test_indexes: list[int] = [1]
for (country_iso_code, country_name), outbounds in country_outbounds.items():
    flag_emoji = (
        ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_iso_code.upper())
        if len(country_iso_code) == 2
        else '🌐'
    )

    test_tag = f'{flag_emoji}{country_name}'
    template['outbounds'].append(
        {
            'type': 'urltest',
            'tag': test_tag,
            'outbounds': [],
            'url': 'http://cp.cloudflare.com/generate_204',
            'interval': '45s',
            'tolerance': 150,
            'idle_timeout': '30m',
            'interrupt_exist_connections': False,
        },
    )
    template['outbounds'][0]['outbounds'].append(test_tag)
    template['outbounds'][1]['outbounds'].append(test_tag)
    test_index = len(template['outbounds']) - 1
    test_indexes.append(test_index)

    for i, outbound in enumerate(outbounds, start=1):
        tag: str = f'[{flag_emoji}{country_name}]-{i} | [{outbound["type"]}]'
        outbound['tag'] = tag
        template['outbounds'][test_index]['outbounds'].append(tag)
        template['outbounds'].append(outbound)

# 排序
template['outbounds'][0]['outbounds'].sort()
for test_index in test_indexes:
    template['outbounds'][test_index]['outbounds'].sort()
template['outbounds'][0]['outbounds'].insert(0, '🌐全部')
template['outbounds'].sort(key=lambda x: x['tag'])


with open('./release_notes.md', 'w', encoding='utf-8') as f:
    f.write("""| 地区 | 节点数量 |
| ---- | -------- |
""")
    for (_, country_name), outbounds in country_outbounds.items():
        f.write(f'| {country_name} | {len(outbounds)} |\n')

with open('./result.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(template, indent=4, ensure_ascii=False))
