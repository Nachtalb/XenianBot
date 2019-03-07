from typing import Iterable

from mongoengine import StringField


class OptionStringField(StringField):

    def __init__(self, options: Iterable[str], **kwargs):
        self.options = options

        kwargs.pop('max_length', None)
        kwargs.pop('min_length', None)
        kwargs.pop('regex', None)

        if not all(map(lambda item: isinstance(item, str), options)):
            raise ValueError('Options are not valid. It must be a Iterable of str\'s.')

        regex = '^('
        for string in options:
            regex += f'{string}|'
        regex = regex.rstrip('|') + ')$'

        super().__init__(regex, **kwargs)

    def in_options(self, string: str) -> bool:
        return string in self.options
