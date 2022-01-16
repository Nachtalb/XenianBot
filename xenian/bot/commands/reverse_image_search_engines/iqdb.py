from .base import ReverseImageSearchEngine

__all__ = ["IQDBReverseImageSearchEngine"]


class IQDBReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for iqdb.org"""

    def __init__(self):
        super(IQDBReverseImageSearchEngine, self).__init__(
            url_base="http://iqdb.org", url_path="?url={image_url}", name="IQDB"
        )
