from telegram import Message, Chat
from telegram.ext import BaseFilter

from xenian.bot import mongodb_database

__all__ = ['custom_db_save_mode']


class CustomDBSaveModeFilter(BaseFilter):
    """Filter save mode on or not

    Attributes:
        custom_db_save_mode (:class:`Collection`): Mongodb collection
    """

    custom_db_save_mode = mongodb_database.custom_db_save_mode

    def filter(self, message: Message) -> bool:
        """Filter save mode on or not

         Args:
            message (:class:`telegram.Message`): The message that is tested.

        Returns:
            :obj:`bool`
        """
        data = self.custom_db_save_mode.find_one({'chat_id': message.chat.id})
        return data['mode'] if data else False


custom_db_save_mode = CustomDBSaveModeFilter()
