import json
import logging
from ipaddress import ip_address

from dns.resolver import NoAnswer, Resolver
from geoip2.database import Reader

from proxy import OutBounds, load_result

with open('./src/template.json', 'r', encoding='utf-8') as f:
    template: dict = json.loads(f.read())


country_outbounds: dict[str, OutBounds] = {}
seen_keys: dict[str, set[str]] = {}

# 筛选可用的节点并按照国家分类
with Reader('Country.mmdb') as geo_reader:
    resolver = Resolver()
    for outbound in load_result():
        try:
            outbound.pop('tag', None)
            if outbound['type'] == 'anytls':
                continue
            ip = outbound['server']

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

            dedup_key = json.dumps(outbound, sort_keys=True, ensure_ascii=False)

            if country_code not in seen_keys:
                seen_keys[country_code] = set()
            if dedup_key in seen_keys[country_code]:
                continue  # 重复，跳过
            seen_keys[country_code].add(dedup_key)

            country_outbounds.setdefault(country_code, []).append(outbound)
        except NoAnswer:  # 不可用
            continue
        except Exception:
            logging.exception('获取节点失败')
            continue

# 添加到模板
for country_code, outbounds in country_outbounds.items():
    template['outbounds'].append(
        {
            'type': 'urltest',
            'tag': f'{country_code}-test',
            'outbounds': [],
            'url': 'http://cp.cloudflare.com/generate_204',
            'interval': '45s',
            'tolerance': 25,
            'idle_timeout': '12m',
            'interrupt_exist_connections': True,
        },
    )
    template['outbounds'][0]['outbounds'].append(f'{country_code}-test')
    test_index = len(template['outbounds']) - 1

    for i, outbound in enumerate(outbounds, start=1):
        flag_emoji = (
            ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper())
            if country_code and len(country_code) == 2
            else '🌐'
        )
        tag: str = f'{flag_emoji} | {country_code} | [{outbound["type"]}]-{i}'
        outbound['tag'] = tag
        template['outbounds'][test_index]['outbounds'].append(tag)
        template['outbounds'].append(outbound)
# 排序
# template['outbounds'][0]['outbounds'].sort()
# template['outbounds'][1]['outbounds'].sort()
# template['outbounds'].sort(key=lambda x: x['tag'])

with open('./release_notes.md', 'w', encoding='utf-8') as f:
    f.write("""| 类型 | 节点数量 |
| ---- | -------- |
""")
    for tag, outbound in country_outbounds.items():
        f.write(f'| {tag} | {len(outbound)} |\n')

with open('./result.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(template, indent=4, ensure_ascii=False))
