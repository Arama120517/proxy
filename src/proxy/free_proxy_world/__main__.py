import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from proxy import OutBound, get_session


def get_href_param(tag, param_name):
    """从标签的 href 属性中提取指定的查询参数"""
    if not tag or not tag.has_attr('href'):
        return None

    href = tag['href']
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    return query_params.get(param_name, [None])[0]


session = get_session()

results: list[OutBound] = []

index: int = 1
timeout: bool = False
while not timeout:
    soup = BeautifulSoup(
        session.get(
            f'https://www.freeproxy.world?type=&anonymity=&country=&speed=600&port=&page={index}'
        ).text,
        'html.parser',
    )

    for row in soup.find_all('tr'):
        cols = row.find_all('td')

        if not cols or len(cols) < 8:  # 确保至少有 8 列
            continue

        total_minutes = 0
        for value, unit in re.findall(r'(\d+)\s*([dh]\.?|minutes)', cols[7].get_text(strip=True)):
            val = int(value)
            if 'd' in unit:
                total_minutes += val * 24 * 60
            elif 'h' in unit:
                total_minutes += val * 60
            elif 'minutes' in unit:
                total_minutes += val
        if total_minutes > 120:
            timeout = True
            break

        if get_href_param(cols[2].find('a'), 'country') == 'CN':
            continue

        result: dict[str, Any] = {
            'server': cols[0].get_text(strip=True),
            'server_port': int(get_href_param(cols[1].find('a'), 'port')),
        }

        match get_href_param(cols[5].find('a'), 'type'):
            case 'http':
                result['type'] = 'http'
            case 'https':
                result['type'] = 'http'
                result['tls'] = {
                    'enabled': True,
                    'insecure': True,
                    'utls': {'enabled': True, 'fingerprint': 'chrome'},
                }
            case 'socks5':
                result['type'] = 'socks'
                result['version'] = '5'
            case 'socks4':
                result['type'] = 'socks'
                result['version'] = '4'

        results.append(result)
    index += 1

with open('./results/free_proxy_world.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)
