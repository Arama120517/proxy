import json
import os
import re

from dns.rdatatype import TXT
from dns.resolver import Resolver
from requests import Response, Session

from proxy import OutBound, get_session

session: Session = get_session()

resolver: Resolver = Resolver()
resolver.nameservers = ['8.8.8.8', '8.8.4.4']

# 登录
api_url: str = resolver.resolve('v3.jego.club', TXT)[0].to_text().strip('"') + '/chrome'
response: Response = session.post(
    f'{api_url}/options/login',
    data={
        'username': os.environ['JEGOCLOUD_USERNAME'],
        'password': os.environ['JEGOCLOUD_PASSWORD'],
    },
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
)
response.raise_for_status()
response: dict = response.json()
token: str = response['session']['token']

# 获取节点ip和端口
response: Response = session.get(f'{api_url}/popup', params={'token': token})
response.raise_for_status()
response: dict = response.json()

data: set[dict] = set(
    re.findall(
        r'HTTPS\s+(?P<host>[\w.-]+\.[a-zA-Z]{2,}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<port>\d+)',
        response['session']['proxy_settings']['value']['pacScript']['data'],
    )
)

if not data:
    raise RuntimeError('正则表达式没有匹配到任何节点')

results: list[OutBound] = []
for host, port in data:
    results.append({
        'type': 'http',
        'server': host,
        'server_port': int(port),
        'tls': {
            'enabled': True,
            'insecure': True,
            'utls': {'enabled': True, 'fingerprint': 'chrome'},
        },
    })

with open('./results/jegocloud.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)
