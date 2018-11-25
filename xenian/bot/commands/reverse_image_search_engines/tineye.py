import requests
from bs4 import BeautifulSoup

from . import ReverseImageSearchEngine

__all__ = ['TinEyeReverseImageSearchEngine']


class TinEyeReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for tineye.com
    """

    def __init__(self):
        super(TinEyeReverseImageSearchEngine, self).__init__(
            url_base='https://tineye.com',
            url_path='/search?url={image_url}',
            name='TinEye'
        )

    @property
    def best_match(self) -> dict:
        if not self.search_html:
            if not self.search_url:
                raise ValueError('No image given yet!')
            self.get_html(self.search_url)
        soup = BeautifulSoup(self.search_html, 'html.parser')

        match = soup.find('div', {'class', 'match'})
        if not match:
            return
        image_url = match.find('p', {'class': 'image-link'}).find('a').get('href')

        if not self.check_image_availability(image_url):
            match = match.find_next('div', {'class', 'match'})
            if not match:
                return
            image_url = match.find('p', {'class': 'image-link'}).find('a').get('href')
            if not self.check_image_availability(image_url):
                return

        match_row = match.find_parent('div', {'class': 'match-row'})
        match_thumb = match_row.find('div', {'class': 'match-thumb'})
        info = match_thumb.find('p').text
        info = [element.strip() for element in info.split(',')]

        return {
            'thumbnail': match_thumb.find('img').get('src'),
            'website_name': match.find('h4').text,
            'website': match.find('span', text='Found on: ').find_next('a').get('href'),
            'image_url': image_url,
            'type': info[0],
            'size': {
                'width': int(info[1].split('x')[0]),
                'height': int(info[1].split('x')[1])
            },
            'volume': info[2],
            'provided by': '[TinEye](https://tineye.com/)',
        }

    def check_image_availability(self, url: str) -> bool:
        """Check if image is still available

        Args:
            url (:obj:`str`): Url to image to check
        Returns:
            :obj:`bool`: True if image is available, False if not
        """
        try:
            return requests.head(url) == 200
        except:
            return False
