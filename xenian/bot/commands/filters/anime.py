from telegram import Message
from telegram.ext import BaseFilter

from xenian.bot.models import TgUser

__all__ = ['anime_save_mode']


class AnimeSaveModeFilter(BaseFilter):
    """Filter sace mode on or not

    Attributes:
        gif_save_mode (:class:`Collection`): Mongodb collection
    """

    def filter(self, message: Message) -> bool:
        """Filter save mode on or not

         Args:
            message (:class:`telegram.Message`): The message that is tested.

        Returns:
            :obj:`bool`
        """
        user = TgUser.from_object(message.from_user)
        return user.giv_save_mode


anime_save_mode = AnimeSaveModeFilter()
