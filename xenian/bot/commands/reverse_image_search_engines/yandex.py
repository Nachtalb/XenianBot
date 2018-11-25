from . import ReverseImageSearchEngine

__all__ = ['YandexReverseImageSearchEngine']


class YandexReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for yandex.com
    """

    def __init__(self):
        super(YandexReverseImageSearchEngine, self).__init__(
            url_base='https://yandex.com',
            url_path='/images/search?url={image_url}&rpt=imageview',
            name='Yandex'
        )
