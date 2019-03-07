from mongoengine import BooleanField, LongField, StringField
from telegram import User

from xenian.bot import settings
from xenian.bot.models.telegram import TelegramDocument

__all__ = ['TgUser']


class TgUser(TelegramDocument):
    meta = {'collection': 'telegram_user'}

    class Meta:
        original = User

    id = LongField(primary_key=True)

    first_name = StringField()
    is_bot = BooleanField()
    username = StringField()
    language_code = StringField()

    download_mode = BooleanField(default=False)
    download_zip_mode = BooleanField(default=False)
    giv_save_mode = BooleanField(default=False)
    is_bot_admin = BooleanField(default=False)
    is_bot_supporter = BooleanField(default=False)

    def __repr__(self):
        return f'{super().__repr__()} - {self.username or self.first_name or str(self.id)}'

    def save(self, *args, **kwargs):
        if self.username in settings.ADMINS:
            self.is_bot_admin = True
        if self.username in settings.SUPPORTER:
            self.is_bot_supporter = True

        super().save(*args, **kwargs)
