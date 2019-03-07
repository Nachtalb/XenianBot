from typing import Generator

from mongoengine import BooleanField, DictField, LongField, ReferenceField
from telegram import Message, TelegramObject

from xenian.bot.models.telegram import TelegramDocument
from xenian.bot.models.tg_chat import TgChat
from xenian.bot.models.tg_user import TgUser

__all__ = ['TgMessage']


class TgMessage(TelegramDocument):
    meta = {'collection': 'telegram_message'}
    file_types = [
        'audio',
        'sticker',
        'video',
        'animation',
        'photo',
        'document',
        'voice',
        'video_note',
    ]
    _file_id = None

    class Meta:
        original = Message
        pk_name = 'message_id'

    message_id = LongField()

    chat = ReferenceField(TgChat)
    from_user = ReferenceField(TgUser)

    original_object = DictField()

    reactions = DictField()

    is_current_message = BooleanField(default=False)

    @classmethod
    def from_object(cls, obj: Message, **kwargs):
        chat = TgChat.from_object(obj.chat)
        return super().from_object(obj, use_pk=False, chat=chat, message_id=obj.message_id)

    def __repr__(self):
        return f'{super().__repr__()} - {self.message_id}:{self.chat.id}'

    @property
    def file_ids(self) -> Generator[int, None, None]:
        if self._file_id is not None:
            yield from self._file_id
            return

        self._file_id = []
        message = self.original_object

        if not message:
            return

        for file_type in self.file_types:
            file = message.get(file_type, None)
            if isinstance(file, list):
                for file_dict in file:
                    self._file_id.append(file_dict['file_id'])
            elif isinstance(file, dict) and 'file_id' in file:
                self._file_id.append(file['file_id'])

        yield from self._file_id

    def is_any_type_of(self, *types: str) -> str or None:
        if isinstance(types, str):
            types = [types]

        for type in types:
            if self.original_object.get(type):
                return type
