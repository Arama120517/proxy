import re

from bs4 import BeautifulSoup
from requests import Response

from proxy import dump_result, get_session

_session: Response = get_session()

_response: Response = _session.get('https://www.freeclashnode.com')
_response.raise_for_status()

_response: Response = _session.get(
    'https://www.freeclashnode.com/'
    + BeautifulSoup(_response.text, 'html.parser').find_all(
        'a',
        class_='list-image-box',
    )[0]['href']
)
_response.raise_for_status()

_response: Response = _session.get(
    f'https://clash2sfa.xmdhs.com/sub?sub={
        "|".join(
            f"{item}"
            for item in re.findall(r'https?://[^\s<>"\']+?\.(?:yaml|json|txt)', _response.text)
        )
    }'
)
_response.raise_for_status()

dump_result(_response.json())
