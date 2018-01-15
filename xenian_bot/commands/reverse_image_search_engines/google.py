from . import ReverseImageSearchEngine

__all__ = ['GoogleReverseImageSearchEngine']


class GoogleReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for google.com"""

    def __init__(self):
        super(GoogleReverseImageSearchEngine, self).__init__(
            url_base='https://www.google.com',
            url_path='/searchbyimage?&image_url={image_url}',
            name='Google'
        )
