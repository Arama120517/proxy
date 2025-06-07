import os
import re
import subprocess
from uuid import uuid4

from dns.rdatatype import TXT
from dns.resolver import Resolver
from requests import RequestException, Response

from src import BaseSource, OutBounds


class JegoCloudSource(BaseSource):
    """https://jegocloud.com"""

    def __init__(self) -> None:
        super().__init__()

        self.token: str = os.environ.get('JEGOCLOUD_TOKEN')
        self.username: str = os.environ.get('JEGOCLOUD_USERNAME')
        self.password: str = os.environ.get('JEGOCLOUD_PASSWORD')

        self.resolver: Resolver = Resolver()
        self.resolver.nameservers = ['8.8.8.8', '8.8.4.4']

        urls: list[str] = []
        for api_url in [
            'https://*.statichuawei.com',
            'https://*.taintedge.com:2019',
            'http://*.cdnfeishu.com',
            'https://*.y62i.com',
        ]:
            urls.append(api_url.replace('*', str(uuid4())))

        urls.append(self.resolver.resolve('v3.jego.club', TXT)[0].to_text().strip('"'))

        for url in urls:
            try:
                response: Response = self.post(
                    f'{url}/chrome/session', data={'token': self.token}, timeout=5
                )
                response.raise_for_status()
            except RequestException:
                self.logger.warning(f'API不可用: {url}')
                urls.remove(url)
                continue

        self.api_url: str = f'{urls[0]}/chrome'

    def get_outbounds(self) -> OutBounds:
        response: Response = self.get(f'{self.api_url}/popup', params={'token': self.token})
        response.raise_for_status()
        response: dict = response.json()

        if not response['session']['proxy_settings'].get('pacScript'):
            self.logger.warning('Token失效, 尝试重新获取Token')
            response: Response = self.post(
                f'{self.api_url}/options/login',
                data={'username': self.username, 'password': self.password},
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            )
            response.raise_for_status()
            response: dict = response.json()
            token: str = response['session']['token']
            subprocess.check_call(
                ['gh', 'secret', 'set', 'JEGOCLOUD_TOKEN', '--app', 'actions', '--body', token],
            )

        data: set[dict] = set(
            re.findall(
                r'HTTPS\s+(?P<host>[\w.-]+\.[a-zA-Z]{2,}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<port>\d+)',
                response['session']['proxy_settings']['value']['pacScript']['data'],
            )
        )

        if not data:
            raise RuntimeError('正则表达式没有匹配到任何节点')

        outbounds: OutBounds = []
        for index, (host, port) in enumerate(data, start=1):
            outbounds.append({
                'type': 'http',
                'tag': f'jegocloud_{index}',
                'server': host,
                'server_port': int(port),
                'tls': {
                    'enabled': True,
                    'insecure': True,
                    'utls': {
                        'fingerprint': 'chrome',
                    },
                },
            })
        return outbounds


if __name__ == '__main__':
    JegoCloudSource().main()
