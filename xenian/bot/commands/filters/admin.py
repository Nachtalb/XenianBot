from telegram import Chat, Message
from telegram.ext import BaseFilter

from xenian.bot.settings import ADMINS
from xenian.bot.utils.telegram import user_is_admin_of_group

__all__ = ['bot_admin', 'bot_group_admin', 'user_group_admin', 'reply_user_group_admin', 'all_admin_group',
           'user_group_admin_if_group']


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

    class UserGroupAdminIfGroup(BaseFilter):
        def filter(self, message: Message) -> bool:
            """Check if the current user is admin of the [current] group if the current chat is a group
            """
            if message.chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
                return user_is_admin_of_group(message.chat, message.from_user)
            return True

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
user_group_admin_if_group = AdminFilter.UserGroupAdminIfGroup()
