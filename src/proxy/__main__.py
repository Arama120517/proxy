import json
from ipaddress import ip_address

from dns.resolver import NoAnswer, Resolver
from geoip2.database import Reader
from geoip2.records import Country

from proxy import OutBounds, load_result

with open('./src/template.json', 'r', encoding='utf-8') as f:
    template: dict = json.loads(f.read())


country_outbounds: dict[Country, OutBounds] = {}
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

            country: Country = geo_reader.country(ip).country

            if country.iso_code == 'CN':
                continue

            dedup_key = json.dumps(outbound, sort_keys=True, ensure_ascii=False)

            if country.iso_code not in seen_keys:
                seen_keys[country.iso_code] = set()
            if dedup_key in seen_keys[country.iso_code]:
                continue  # 重复，跳过
            seen_keys[country.iso_code].add(dedup_key)

            country_outbounds.setdefault(country, [outbound])
        except NoAnswer:  # 不可用
            continue

# 合并数量较小的国家到“其他”
other_outbounds: OutBounds = []
for country, outbounds in list(country_outbounds.items()):
    if len(outbounds) < 5:
        other_outbounds.extend(outbounds)
        del country_outbounds[country]

if other_outbounds:
    country_outbounds[Country(locales=['zh_CN'], iso_code='OTHER', names={'zh_CN': '其他'})] = (
        other_outbounds
    )

# 添加到模板
for country, outbounds in country_outbounds.items():
    flag_emoji = (
        ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country.iso_code.upper())
        if len(country.iso_code) == 2
        else '🌐'
    )
    country_name = country.names.get('zh_CN', country.iso_code)

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
    test_index = len(template['outbounds']) - 1

    for i, outbound in enumerate(outbounds, start=1):
        tag: str = f'{flag_emoji}{country_name} | [{outbound["type"]}]-{i}'
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
