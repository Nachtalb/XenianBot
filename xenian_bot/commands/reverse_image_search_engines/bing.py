from . import ReverseImageSearchEngine

__all__ = ['BingReverseImageSearchEngine']


class BingReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for bing.com
    """

    def __init__(self):
        super(BingReverseImageSearchEngine, self).__init__(
            url_base='https://www.bing.com',
            url_path='/images/search?q=imgurl:{image_url}&view=detailv2&iss=sbi',
            name='Bing'
        )
