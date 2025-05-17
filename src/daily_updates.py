from abc import abstractmethod
from datetime import datetime, timedelta, timezone

from requests import RequestException, Response

from src import ProxyServerGenerator


class _DailyUpdates(ProxyServerGenerator):
    """适配每日在链接更新日期的源"""

    @property
    @abstractmethod
    def url(self) -> str: ...

    def generate(self) -> list[dict]:
        today: datetime = datetime.now(timezone(timedelta(hours=8)))
        rollback_days: int = 0
        for i in range(7):
            time: datetime = today - timedelta(days=rollback_days)
            try:
                response: Response = self.get(
                    time.strftime(self.url),
                )
                response.raise_for_status()
                response: dict = response.json()

                servers: list[dict] = []
                for outbound in response['outbounds']:
                    if 'server' not in outbound:
                        continue
                    servers.append(outbound)
                return servers
            except RequestException:
                self.logger.warning(
                    f'获取节点失败, 尝试获取{time.strftime("%Y %m %d")}的节点'.format(time=time)
                )
                rollback_days += 1
            self.logger.error('获取节点失败')
        return []


class FreeClassNode(_DailyUpdates):
    """https://www.freeclashnode.com"""

    @property
    def url(self) -> str:
        return 'https://node.freeclashnode.com/uploads/%Y/%m/%Y%m%d.json'


class AirPortNodes(_DailyUpdates):
    """https://www.airportnode.com"""

    @property
    def url(self) -> str:
        # Clash.Meta 转换 sing-box
        return 'https://clash2sfa.xmdhs.com/sub?sub=http://airportnode.cczzuu.top/node/%Y%m%d-clash.yaml'
