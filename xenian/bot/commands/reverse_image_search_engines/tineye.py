from .base import ReverseImageSearchEngine

__all__ = ["TinEyeReverseImageSearchEngine"]


class TinEyeReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for tineye.com"""

    def __init__(self):
        super(TinEyeReverseImageSearchEngine, self).__init__(
            url_base="https://tineye.com",
            url_path="/search?url={image_url}",
            name="TinEye",
        )
