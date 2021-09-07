from . import ReverseImageSearchEngine

__all__ = ['TraceReverseImageSearchEngine']


class TraceReverseImageSearchEngine(ReverseImageSearchEngine):
    """A :class:`ReverseImageSearchEngine` configured for trace.moe
    """

    def __init__(self):
        super(TraceReverseImageSearchEngine, self).__init__(
            url_base='https://trace.moe',
            url_path='/?auto&url={image_url}',
            name='Trace'
        )
