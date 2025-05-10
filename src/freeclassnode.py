import json
from datetime import datetime, timedelta, timezone

import requests
from requests import HTTPError, Response
from rich import print_json
from ua_generator import generate

from src import ProxyServerGenerator


class FreeClassNode(ProxyServerGenerator):
    def generate(self) -> list[dict]:
        today: datetime = datetime.now(timezone(timedelta(hours=8)))
        rollback_days: int = 0
        for i in range(7):
            time: datetime = today - timedelta(days=rollback_days)
            try:
                response: Response = requests.get(
                    time.strftime('https://node.freeclashnode.com/uploads/%Y/%m/%Y%m%d.json'),
                    headers={'User-Agent': generate().text},
                )
                response.raise_for_status()
                response: dict = response.json()

                servers: list[dict] = []
                for outbound in response['outbounds']:
                    if 'server' not in outbound:
                        continue
                    servers.append(outbound)
                return servers
            except HTTPError:
                self.logger.warning(
                    f'获取节点失败, 尝试获取{time.strftime("%Y %m %d")}的节点'.format(time=time)
                )
                rollback_days += 1
            self.logger.error('获取节点失败')
            return []


if __name__ == '__main__':
    print_json(json.dumps(FreeClassNode()), indent=4, ensure_ascii=False)
