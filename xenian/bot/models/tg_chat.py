from mongoengine import BooleanField, LongField, StringField, DictField
from telegram import Chat

from xenian.bot.models.fields.option_string_field import OptionStringField
from xenian.bot.models.telegram import TelegramDocument

__all__ = ['TgChat']


class TgChat(TelegramDocument):
    meta = {'collection': 'telegram_chat'}

    class Meta:
        original = Chat
        load_self = 'get_chat'

    id = LongField(primary_key=True)

    type = OptionStringField(['private', 'channel', 'group', 'supergroup'])
    all_members_are_administrators = BooleanField(default=False)

    title = StringField(default='')
    first_name = StringField(default='')
    username = StringField(default='')

    group_rules = StringField(default='')
    group_warnings = DictField(default={})  # {int(user_id): int(number_of_warnings)}

    def __repr__(self):
        return f'{super().__repr__()} - {self.username or self.title or str(self.id)}'
