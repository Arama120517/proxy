import json
import re

from bs4 import BeautifulSoup
from requests import HTTPError, Response, Session

from proxy import OutBound, get_session

session: Session = get_session()

response: Response = session.get('https://www.freeclashnode.com')
response.raise_for_status()

# 获取最新的页面
page: str = BeautifulSoup(response.text, 'html.parser').find_all(
    'a',
    class_='list-image-box',
)[0]['href']  # ty:ignore[invalid-assignment]

response: Response = session.get(f'https://www.freeclashnode.com/{page}')
response.raise_for_status()

results: list[OutBound] = []
for item in re.findall(r'https?://[^\s<>"\']+?\.(?:yaml|json|txt)', response.text):
    try:
        response: Response = session.get(f'https://clash2sfa.xmdhs.com/sub?sub={f"{item}"}')
        response.raise_for_status()
        results += response.json()['outbounds']
    except HTTPError as e:  # 可能是服务器问题, 有时候获取的yaml文件会报错520
        if e.response.status_code >= 500:
            continue

with open('./results/free_clash_node.json', 'w', encoding='utf-8') as f:
    json.dump([r for r in results if 'server' in r], f, ensure_ascii=False, indent=4)
