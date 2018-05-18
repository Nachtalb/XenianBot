from telegram import Message
from telegram.ext import BaseFilter
from xenian_bot.settings import ADMINS


__all__ = ['bot_admin', 'bot_group_admin', 'user_group_admin', 'reply_user_group_admin', 'all_admin_group']


def user_is_admin_of_group(chat, user):
    """Check if the given user is admin of the chat

    Attributes:
        chat (:obj:`Chat`): Telegram Chat Object
        user (:obj:`User`): Telegram User Object
    """
    if chat.all_members_are_administrators:
        return True

    for member in chat.get_administrators():
        if user == member.user:
            return True
    return False


class AdminFilter:
    """Various "is admin of" filters
    """

    class BotAdmin(BaseFilter):
        def filter(self, message: Message) -> bool:
            """Check if current user is admin of the bot
            """
            return '@' + message.from_user.username in ADMINS

    class BotGroupAdmin(BaseFilter):
        def filter(self, message: Message) -> bool:
            """Check if this bot is admin of the [current] group
            """
            me = message.bot.get_me()
            return user_is_admin_of_group(message.chat, me)

    class UserGroupAdmin(BaseFilter):
        def filter(self, message: Message) -> bool:
            """Check if the current user is admin of the [current] group
            """
            return user_is_admin_of_group(message.chat, message.from_user)

    class ReplyUserGroupAdmin(BaseFilter):
        def filter(self, message: Message) -> bool:
            """Check the user replying to is admin in the [current] group
            """
            if message.reply_to_message:
                return user_is_admin_of_group(message.chat, message.reply_to_message.from_user)
            return False

    class AllAdminGroup(BaseFilter):
        def filter(self, message: Message) -> bool:
            """Check if in the [current] group "all are admins" is active
            """
            return bool(message.chat.all_members_are_administrators)


bot_admin = AdminFilter.BotAdmin()
bot_group_admin = AdminFilter.BotGroupAdmin()
user_group_admin = AdminFilter.UserGroupAdmin()
reply_user_group_admin = AdminFilter.ReplyUserGroupAdmin()
all_admin_group = AdminFilter.AllAdminGroup()
