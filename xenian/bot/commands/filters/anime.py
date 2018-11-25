from telegram import Message
from telegram.ext import BaseFilter

from xenian.bot import mongodb_database

__all__ = ['anime_save_mode']


class AnimeSaveModeFilter(BaseFilter):
    """Filter sace mode on or not

    Attributes:
        gif_save_mode (:class:`Collection`): Mongodb collection
    """

    gif_save_mode = mongodb_database.gif_save_mode

    def filter(self, message: Message) -> bool:
        """Filter save mode on or not

         Args:
            message (:class:`telegram.Message`): The message that is tested.

        Returns:
            :obj:`bool`
        """
        data = self.gif_save_mode.find_one({'chat_id': message.chat_id})
        return data['mode'] if data else False


anime_save_mode = AnimeSaveModeFilter()
