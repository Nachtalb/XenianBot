import re

from bs4 import BeautifulSoup

from . import ReverseImageSearchEngine

__all__ = ['IQDBReverseImageSearchEngine']


class IQDBReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for iqdb.org"""

    def __init__(self):
        super(IQDBReverseImageSearchEngine, self).__init__(
            url_base='http://iqdb.org',
            url_path='?url={image_url}',
            name='iqdb'
        )

    @property
    def best_match(self):
        if not self.search_html:
            if not self.search_url:
                raise ValueError('No image given yet!')
            self.get_html(self.search_url)
        soup = BeautifulSoup(self.search_html, "html.parser")
        best_match = soup.find('th', text='Best match')

        if not best_match:
            return
        table = best_match.find_parent('table')
        size_match = re.match('\d*×\d*', table.find('td', text=re.compile('×')).text)
        size = size_match[0]
        safe = size_match.string.replace(size, '').strip(' []')

        website = table.select('td.image a')[0].attrs['href']
        if not website.startswith('http'):
            website = 'http://' + website.lstrip('/ ')
        best_match = {
            'thumbnail': self.url_base + table.select('td.image img')[0].attrs['src'],
            'website': website,
            'website_name': table
                .find('img', {'class': 'service-icon'})
                .find_parent('td')
                .find(text=True, recursive=False)
                .strip(),
            'size': {
                'width': int(size.split('×')[0]),
                'height': int(size.split('×')[1])
            },
            'sfw': safe,
            'similarity': float(re.match('\d*', table.find('td', text=re.compile('similarity')).text)[0]),
            'provided by': '[IQDB](http://iqdb.org/)',
        }

        return best_match
