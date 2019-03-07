from telegram import Message
from telegram.ext import BaseFilter

from xenian.bot.models import TgUser

__all__ = ['download_mode_filter']


class DownloadMode(BaseFilter):
    """Filter which manages the download mode for each user
    """

    def filter(self, message: Message) -> bool:
        """Filter download_mode on or not

         Args:
            message (:class:`telegram.Message`): The message that is tested.

        Returns:
            :obj:`bool`
        """
        user = TgUser.from_object(message.from_user)
        return user.download_mode


download_mode_filter = DownloadMode()
