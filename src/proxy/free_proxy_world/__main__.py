import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from proxy import OutBounds, dump_result, get_session


def get_href_param(tag, param_name):
    """从标签的 href 属性中提取指定的查询参数"""
    if not tag or not tag.has_attr('href'):
        return None

    href = tag['href']
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    return query_params.get(param_name, [None])[0]


session = get_session()

results: OutBounds = []

index = 1
total_minutes = 0
while total_minutes < 30:
    soup = BeautifulSoup(
        session.get(f'https://www.freeproxy.world?page={index}').text, 'html.parser'
    )

    for row in soup.find_all('tr'):
        total_minutes = 0

        cols = row.find_all('td')

        if not cols or len(cols) < 8:  # 确保至少有 8 列
            continue

        if int(get_href_param(cols[4].find('a'), 'speed')) > 300:
            continue

        for value, unit in re.findall(r'(\d+)\s*([dh]\.?|minutes)', cols[7].get_text(strip=True)):
            val = int(value)
            if 'd' in unit:
                total_minutes += val * 24 * 60
            elif 'h' in unit:
                total_minutes += val * 60
            elif 'minutes' in unit:
                total_minutes += val
        if total_minutes > 60:
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
                    'utls': {
                        'fingerprint': 'chrome',
                    },
                }
            case 'socks5':
                result['type'] = 'socks'
                result['version'] = '5'
                result['udp'] = True
            case 'socks4':
                result['type'] = 'socks'
                result['version'] = '4'

        results.append(result)
    index += 1

dump_result(results)
