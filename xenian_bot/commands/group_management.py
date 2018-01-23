import datetime

from telegram import Bot, Update

import xenian_bot
from xenian_bot.commands import BaseCommand
from xenian_bot.utils import data, get_self

__all__ = ['group_manager']


class GroupManager(BaseCommand):
    """Roll a dice
    """

    group_data_set = 'group_management'

    def __init__(self):
        self.commands = [
            {
                'title': 'Ban',
                'description': 'Ban a user. Reply to one of his messages with this command (Group Only)',
                'command': self.ban
            },
            {
                'title': 'Strike',
                'description': 'Warn a user, after 3 warnings he get banned. Reply to one of his messages with this '
                               'command (Group Only)',
                'command': self.warn
            },
            {
                'title': 'Kick',
                'description': 'Kick a user for 10 min. Reply to one of his messages with this command (Group Only)',
                'command': self.kick
            }
        ]

        super(GroupManager, self).__init__()

    def get_admin_ids(self, bot: Bot, chat_id: int) -> list:
        """Returns a list of admin IDs for a given chat.

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            chat_id (:obj:`int`): The id of the chat

        Returns:
            :obj:`list`: A list with the admins IDs
        """
        return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]

    def is_allowed(self, bot: Bot, update: Update) -> bool:
        """Check if bot is allowed to do banning and warning

        If the bot is not allowed to do so, a message will automatically sent to the group why he couldn't do it.

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object

        Returns:
            :obj:`bool`: True if the bot is allowed, false otherwise
        """
        if update.message.chat.type not in ['group', 'supergroup']:
            update.message.reply_text('This command only works in groups')
            return False

        wanted_user = update.message.reply_to_message.from_user
        from_user = update.message.from_user

        admins_in_group = self.get_admin_ids(bot, update.effective_chat.id)
        this_bot = get_self(bot)

        if this_bot.id not in admins_in_group:
            if from_user.id in admins_in_group:
                update.message.reply_text('I cannot do this as long as I am not admin.'.format(
                    username=from_user.username))
            else:
                update.message.reply_text('@{username} is not allowed to run this command.'.format(
                    username=update.message.from_user.username))
        elif wanted_user.id in admins_in_group:
            update.message.reply_text('This command cannot be used on admins like @{username}.'.format(
                username=wanted_user.username))
        elif update.message.chat.all_members_are_administrators:
            update.message.reply_text('I cannot do this in a group where all members are admin.')
        else:
            return True
        return False

    def kick(self, bot: Bot, update: Update, is_allowed: bool = False):
        """Kick a user for 30 sec

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            is_allowed (:obj:`bool`, optional): If the is_allowed check was already run so you don't have to again
        """
        if update.message.reply_to_message is None:
            update.message.reply_text('You have to reply to a message from this user to kick him.')
            return

        chat_id = update.message.chat_id
        from_user = update.message.from_user
        wanted_user = update.message.reply_to_message.from_user
        if is_allowed or self.is_allowed(bot, update):
            now = datetime.datetime.now()

            bot.kick_chat_member(
                chat_id=chat_id,
                user_id=wanted_user.id,
                until_date=now + datetime.timedelta(minutes=10))

            xenian_bot.job_queue.run_once(
                callback=(
                    lambda bot, job: bot.send_message(
                        chat_id,
                        '@{wanted_user.username} was kicked 10 min ago and can now join again'.format(
                            wanted_user=wanted_user))),
                when=10 * 60)

            bot.send_message(
                chat_id=chat_id,
                text='@{wanted_user.username} was kicked for 10 min by @{from_user.username}'.format(
                    from_user=from_user,
                    wanted_user=wanted_user))

    def ban(self, bot: Bot, update: Update, is_allowed: bool = False):
        """Ban a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            is_allowed (:obj:`bool`, optional): If the is_allowed check was already run so you don't have to again
        """
        if update.message.reply_to_message is None:
            update.message.reply_text('You have to reply to a message from this user to ban him.')
            return

        chat_id = update.message.chat_id
        from_user = update.message.from_user
        wanted_user = update.message.reply_to_message.from_user
        if is_allowed or self.is_allowed(bot, update):
            group_data = data.get(self.group_data_set)

            if not group_data.get(chat_id, None):
                group_data[chat_id] = {}
            if not group_data[chat_id].get(wanted_user.id, None):
                group_data[chat_id][wanted_user.id] = 'banned'
            else:
                if group_data[chat_id][wanted_user.id] == 'banned':
                    bot.send_message(
                        chat_id=chat_id,
                        text='@{wanted_user.username} was already banned.'.format(wanted_user=wanted_user))
                    return
                else:
                    group_data[chat_id][wanted_user.id] = 'banned'

            now = datetime.datetime.now()

            bot.kick_chat_member(
                chat_id=chat_id,
                user_id=wanted_user.id,
                until_date=now + datetime.timedelta(seconds=5))
            bot.send_message(
                chat_id=chat_id,
                text='@{wanted_user.username} was banned by @{from_user.username}'.format(
                    from_user=from_user,
                    wanted_user=wanted_user))

            data.save(self.group_data_set, group_data)

    def warn(self, bot: Bot, update: Update):
        """Strike a user

        After 3 strikes he is banned

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if update.message.reply_to_message is None:
            update.message.reply_text('You have to reply to a message from this user to warn him.')
            return
        chat_id = update.message.chat_id
        from_user = update.message.from_user
        wanted_user = update.message.reply_to_message.from_user
        if self.is_allowed(bot, update):
            group_data = data.get(self.group_data_set)

            if not group_data.get(chat_id, None):
                group_data[chat_id] = {}
            if not group_data[chat_id].get(wanted_user.id, None):
                group_data[chat_id][wanted_user.id] = 1
            else:
                if group_data[chat_id][wanted_user.id] == 'banned':
                    bot.send_message(
                        chat_id=chat_id,
                        text='@{wanted_user.username} was already banned.'.format(wanted_user=wanted_user))
                    return
                else:
                    group_data[chat_id][wanted_user.id] += 1
            if group_data[chat_id][wanted_user.id] == 3:
                self.ban(bot, update, True)
                return

            bot.send_message(
                chat_id=chat_id,
                text=('@{wanted_user.username} was warned by @{from_user.username}\n'
                      'User has now {warns} waning/s. With 3 warnings user gets banned.').format(
                    from_user=from_user,
                    wanted_user=wanted_user,
                    warns=group_data[chat_id][wanted_user.id]))

            data.save(self.group_data_set, group_data)


group_manager = GroupManager()
