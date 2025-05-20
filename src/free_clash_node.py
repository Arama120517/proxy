import re

from bs4 import BeautifulSoup
from requests import Response

from src import BaseSource, OutBounds


class FreeClashNodeSource(BaseSource):
    """https://www.freeclashnode.com"""

    def get_outbounds(self) -> OutBounds:
        response: Response = self.get('https://www.freeclashnode.com')
        response.raise_for_status()

        links: list[str] = []
        for article in BeautifulSoup(response.text, 'html.parser').find_all(
            'a', title=lambda x: x and '订阅链接每天更新' in x
        ):
            links.append(f'https://www.freeclashnode.com/{article["href"]}')

        outbounds: OutBounds = []
        response: Response = self.get(links[0])
        response.raise_for_status()

        be_found_urls: list[str] = re.findall(r'https?://[^\s<>"\']+?\.yaml', response.text)
        if not be_found_urls:
            raise RuntimeError('正则表达式没有匹配到任何链接')

        for url in be_found_urls:
            response: Response = self.get(f'https://clash2sfa.xmdhs.com/sub?sub={url}')
            response.raise_for_status()
            outbounds += self.extract_proxy_servers(response.json())
        return outbounds


if __name__ == '__main__':
    FreeClashNodeSource().test()
