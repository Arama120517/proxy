import json
import socket
from ipaddress import ip_address

from dns.resolver import NoAnswer, Resolver
from geoip2.database import Reader
from geoip2.records import Country

from proxy import OutBounds, load_result

with open('./src/template.json', 'r', encoding='utf-8') as f:
    template: dict = json.loads(f.read())

country_outbounds: dict[tuple[str, str], OutBounds] = {}

seen_keys: set[str] = set()

# 筛选可用的节点并按照国家分类
with Reader('Country.mmdb') as geo_reader:
    resolver = Resolver()
    for outbound in load_result():
        try:
            outbound.pop('tag', None)

            dedup_key = json.dumps(outbound, sort_keys=True, ensure_ascii=False)
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            if outbound['type'] == 'anytls':
                continue
            ip = outbound['server']

            try:
                ip_address(address=ip)
            except ValueError:
                try:
                    ip = socket.gethostbyname(ip)
                except socket.gaierror:
                    continue

            country: Country = geo_reader.country(ip).country

            if country.iso_code == 'CN':
                continue

            result_key = country.iso_code, country.names.get('zh-CN', country.iso_code)
            if country.iso_code == 'TW':
                result_key = 'TW', '台湾'

            if result_key not in country_outbounds:
                country_outbounds[result_key] = []
            country_outbounds[result_key].append(outbound)
        except NoAnswer:  # 不可用
            continue

# 添加到模板
test_indexs: list[int] = [1]
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
            'tolerance': 25,
            'idle_timeout': '12m',
            'interrupt_exist_connections': True,
        },
    )
    template['outbounds'][0]['outbounds'].append(test_tag)
    template['outbounds'][1]['outbounds'].append(test_tag)
    test_index = len(template['outbounds']) - 1
    test_indexs.append(test_index)

    for i, outbound in enumerate(outbounds, start=1):
        tag: str = f'[{flag_emoji}{country_name}]-{i} | [{outbound["type"]}]'
        outbound['tag'] = tag
        template['outbounds'][test_index]['outbounds'].append(tag)
        template['outbounds'].append(outbound)

# 排序
template['outbounds'][0]['outbounds'].sort()
for test_index in test_indexs:
    template['outbounds'][test_index]['outbounds'].sort()
template['outbounds'][0]['outbounds'].insert(0, '🌐全部')
template['outbounds'].sort(key=lambda x: x['tag'])


with open('./release_notes.md', 'w', encoding='utf-8') as f:
    f.write("""| 国家 | 节点数量 |
| ---- | -------- |
""")
    for (_, country_name), outbound in country_outbounds.items():
        f.write(f'| {country_name} | {len(outbound)} |\n')

with open('./result.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(template, indent=4, ensure_ascii=False))
