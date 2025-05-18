from bs4 import BeautifulSoup

from src import BaseSource


class FreeClashNodeSource(BaseSource):
    """https://www.freeclashnode.com"""

    def generate(self) -> list[dict]:
        response = self.get('https://www.freeclashnode.com')
        response.raise_for_status()

        links = []
        for article in BeautifulSoup(response.text, 'html.parser').find_all(
            'a', title=lambda x: x and '订阅链接每天更新' in x
        ):
            links.append(f'https://www.freeclashnode.com/{article["href"]}')

        servers = []
        for source in self.from_website_get_source_urls(links[0], 'yaml'):
            servers += self.from_clash_source_get_proxy_servers(source)
        return servers
