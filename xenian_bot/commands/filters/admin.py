from telegram import Message
from telegram.ext import BaseFilter
from xenian_bot.settings import ADMINS


__all__ = ['bot_admin']


class BotAdminFilter(BaseFilter):
    """If current user is Admin of the bot
    """

    def filter(self, message: Message) -> bool:
        """Check if current user is admin of the bot

         Args:
            message (:class:`telegram.Message`): The message that is tested.

        Returns:
            :obj:`bool`
        """
        return '@' + message.from_user.username in ADMINS


bot_admin = BotAdminFilter()
