import re
from datetime import datetime, timedelta, timezone

from requests import RequestException, Response

from src import ProxyServerGenerator


class V2RayNews(ProxyServerGenerator):
    """https://v2raynews.com"""

    def generate(self) -> list[dict]:
        today: datetime = datetime.now(timezone(timedelta(hours=8)))
        rollback_days: int = 0
        for i in range(7):
            time: datetime = today - timedelta(days=rollback_days)
            try:
                response: Response = self.get(
                    time.strftime('https://v2raynews.com/free-nodes-%Y%#m%#d'),
                )
                response.raise_for_status()

                be_found_url = re.search(
                    r'https://dlconf\.clashapps\.cc/yaml/[a-zA-Z0-9\-]+\.yaml', response.text
                )
                if not be_found_url:
                    raise RuntimeError('正则表达式没有匹配到任何链接')

                response = self.get(f'https://clash2sfa.xmdhs.com/sub?sub={be_found_url.group()}')
                response.raise_for_status()

                servers: list[dict] = []
                for outbound in response.json()['outbounds']:
                    if 'server' not in outbound:
                        continue
                    servers.append(outbound)
                return servers
            except RequestException:
                self.logger.warning(
                    f'获取节点失败, 尝试获取{time.strftime("%Y-%m-%d")}的节点'.format(time=time)
                )
                rollback_days += 1
        return []


if __name__ == '__main__':
    import json

    from rich import print_json

    print_json(json.dumps(V2RayNews().generate()), indent=4, ensure_ascii=False)
