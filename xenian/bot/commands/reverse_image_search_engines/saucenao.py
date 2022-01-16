from .base import ReverseImageSearchEngine

__all__ = ["SauceNaoReverseImageSearchEngine"]


class SauceNaoReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`SauceNaoReverseImageSearchEngine` configured for iqdb.org"""

    def __init__(self):
        super(SauceNaoReverseImageSearchEngine, self).__init__(
            url_base="https://saucenao.com",
            url_path="/search.php?url={image_url}",
            name="SauceNAO",
        )
