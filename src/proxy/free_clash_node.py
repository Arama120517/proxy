import re
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup
from requests import Response

from proxy import BaseSource, OutBounds


class FreeClashNodeSource(BaseSource):
    """https://www.freeclashnode.com"""

    time: datetime

    def __init__(self):
        super().__init__()
        self.time = datetime.now(timezone(timedelta(), 'Asia/Shanghai'))

    def get_outbounds(self) -> OutBounds:
        response: Response = self.get('https://www.freeclashnode.com')
        response.raise_for_status()

        links: list[str] = []
        for article in BeautifulSoup(response.text, 'html.parser').find_all(
            'a',
            class_='list-image-box',
        ):
            links.append(f'https://www.freeclashnode.com/{article["href"]}')

        response: Response = self.get(links[0])
        response.raise_for_status()

        response: Response = self.get(
            f'https://clash2sfa.xmdhs.com/sub?sub={
                "|".join(
                    f"{item}"
                    for item in re.findall(
                        r'https?://[^\s<>"\']+?\.(?:yaml|json|txt)', response.text
                    )
                )
            }'
        )
        response.raise_for_status()
        return self.extract_proxy_servers(response.json())


if __name__ == '__main__':
    FreeClashNodeSource().main()
