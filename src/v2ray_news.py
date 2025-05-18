from datetime import datetime, timedelta, timezone

from requests import RequestException

from src import BaseSource


class V2RayNews(BaseSource):
    """https://v2raynews.com"""

    def generate(self) -> list[dict]:
        today: datetime = datetime.now(timezone(timedelta(hours=8)))
        rollback_days: int = 0
        for i in range(7):
            time: datetime = today - timedelta(days=rollback_days)
            try:
                return self.from_clash_source_get_proxy_servers(
                    self.from_website_get_source_urls(
                        time.strftime('https://v2raynews.com/free-nodes-%Y%#m%#d'), 'yaml'
                    )[0]
                )
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
