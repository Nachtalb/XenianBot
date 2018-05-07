import datetime

from telegram import Bot, ParseMode, Update, User

import xenian_bot
from xenian_bot.commands import BaseCommand
from xenian_bot.utils import data, get_self, get_user_link

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
                'description': 'Kick a user for 10 min or give a specific amount of time (in min) between 30sec '
                               '(0.5 min) and 366 days (527040 min). Reply to one of his messages with this command '
                               '(Group Only)',
                'args': '[TIME]',
                'options': {'pass_args': True},
                'command': self.kick
            },
            {
                'title': 'Delete and Warn',
                'description': 'Delete a message from a user and warn them. Reply to one of his messages with this '
                               'command (Group Only)',
                'command': self.delete,
            },
            {
                'title': 'Remove Warnings',
                'description': 'Remove all warnings from a User. Reply to one of his messages with this command '
                               '(Group Only)',
                'command': self.unwarn,
            },
            {
                'title': 'Rules',
                'description': 'Show rules for this group (Group Only)',
                'command': self.rules,
            },
            {
                'title': 'Define Rules',
                'description': 'Define rules for this group (Group Only)',
                'args': 'YOUR_RULES',
                'command': self.rules_define,
            },
            {
                'title': 'Remove Rules',
                'description': 'Remove rules for this group (Group Only)',
                'command': self.rules_remove,
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

    def is_admin(self, bot: Bot, update: Update) -> bool:
        """Check if user and bot is admin

              If not send message

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object

        Returns:
            :obj:`bool`: True if the bot is allowed, false otherwise
        """

        from_user = update.message.from_user
        admins_in_group = self.get_admin_ids(bot, update.effective_chat.id)
        this_bot = get_self(bot)

        if this_bot.id not in admins_in_group:
            update.message.reply_text('I cannot do this as long as I am not admin.')
            return False
        elif from_user.id not in admins_in_group:
            update.message.reply_text('{from_user} is not allowed to run this command.'.format(
                from_user=get_user_link(update.message.from_user)),
                parse_mode=ParseMode.MARKDOWN
            )
            return False
        return True

    def in_group(self, update: Update) -> bool:
        """Check if bot is in group

        If not send message

        Args:
            update (:obj:`telegram.update.Update`): Telegram Api Update Object

        Returns:
            :obj:`bool`: True if chat is a group, false otherwise
        """
        if update.message.chat.type not in ['group', 'supergroup']:
            update.message.reply_text('This command only works in groups')
            return False
        return True

    def is_allowed(self, bot: Bot, update: Update) -> bool:
        """Check if bot is allowed to do banning and warning

        If the bot is not allowed to do so, a message will automatically sent to the group why he couldn't do it.

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object

        Returns:
            :obj:`bool`: True if the bot is allowed, false otherwise
        """
        if not self.in_group(update):
            return False

        wanted_user = update.message.reply_to_message.from_user
        admins_in_group = self.get_admin_ids(bot, update.effective_chat.id)

        if not self.is_admin(bot, update):
            return False
        elif wanted_user.id in admins_in_group:
            update.message.reply_text('This command cannot be used on admins like {wanted_user}.'.format(
                wanted_user=get_user_link(wanted_user)),
                parse_mode=ParseMode.MARKDOWN
            )
        elif update.message.chat.all_members_are_administrators:
            update.message.reply_text('I cannot do this in a group where all members are admin.')
        else:
            return True
        return False

    def kick(self, bot: Bot, update: Update, args: list = None, is_allowed: bool = False):
        """Kick a user for 30 sec or a specific amount of time

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): Time in min
            is_allowed (:obj:`bool`, optional): If the is_allowed check was already run so you don't have to again
        """
        if update.message.reply_to_message is None:
            update.message.reply_text('You have to reply to a message from this user to kick him.')
            return

        chat_id = update.message.chat_id
        from_user = update.message.from_user
        wanted_user = update.message.reply_to_message.from_user
        if is_allowed or self.is_allowed(bot, update):
            time = 10
            if args:
                try:
                    time = float(args[0])
                    if not 0.5 <= time <= 527040:
                        update.message.reply_text('Time must be between 30 sec (0.5 min) and 366 days (527040 min).')
                        return
                except ValueError:
                    update.message.reply_text('You have to give me the time in min like `/kick 30`')
                    return

            now = datetime.datetime.now()
            kick_until = now - datetime.timedelta(minutes=time)
            bot.kick_chat_member(
                chat_id=chat_id,
                user_id=wanted_user.id,
                until_date=kick_until)

            xenian_bot.job_queue.run_once(
                callback=(
                    lambda bot, job: bot.send_message(
                        chat_id,
                        '{wanted_user} was kicked {time} min ago and can now join again'.format(
                            time=time,
                            wanted_user=get_user_link(wanted_user)),
                        parse_mode=ParseMode.MARKDOWN)),
                when=10 * 60)

            bot.send_message(
                chat_id=chat_id,
                text='{wanted_user} was kicked for {time} min by {from_user}'.format(
                    time=time,
                    from_user=get_user_link(from_user),
                    wanted_user=get_user_link(wanted_user)),
                parse_mode=ParseMode.MARKDOWN)

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
                        text='{wanted_user} was already banned.'.format(wanted_user=get_user_link(wanted_user)),
                        parse_mode=ParseMode.MARKDOWN)
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
                text='{wanted_user} was banned by {from_user}'.format(
                    from_user=get_user_link(from_user),
                    wanted_user=get_user_link(wanted_user)),
                parse_mode=ParseMode.MARKDOWN)

            data.save(self.group_data_set, group_data)

    def warn(self, bot: Bot, update: Update, wanted_user: User = None):
        """Strike a user

        After 3 strikes he is banned

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            wanted_user (:obj:`telegram.user.User`): Telegram User object of the user which should be warned
        """
        if update.message.reply_to_message is None:
            update.message.reply_text('You have to reply to a message from this user to warn him.')
            return
        chat_id = update.message.chat_id
        from_user = update.message.from_user
        wanted_user = wanted_user or update.message.reply_to_message.from_user
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
                        text='{wanted_user} was already banned.'.format(wanted_user=get_user_link(wanted_user)),
                        parse_mode=ParseMode.MARKDOWN)
                    return
                else:
                    group_data[chat_id][wanted_user.id] += 1
            if group_data[chat_id][wanted_user.id] == 3:
                self.ban(bot, update, True)
                return

            bot.send_message(
                chat_id=chat_id,
                text=('{wanted_user} was warned by {from_user}\n User has now {warns} waning/s. With 3 warnings user '
                      'gets banned.').format(
                    from_user=get_user_link(from_user),
                    wanted_user=get_user_link(wanted_user),
                    warns=group_data[chat_id][wanted_user.id]),
                parse_mode=ParseMode.MARKDOWN)

            data.save(self.group_data_set, group_data)

    def unwarn(self, bot: Bot, update: Update, wanted_user: User = None):
        """Remove all warnings from a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            wanted_user (:obj:`telegram.user.User`): Telegram User object of the user which should be warned
        """
        if update.message.reply_to_message is None:
            update.message.reply_text('You have to reply to a message from a user to warn him.')
            return
        chat_id = update.message.chat_id
        from_user = update.message.from_user
        wanted_user = wanted_user or update.message.reply_to_message.from_user
        if self.is_allowed(bot, update):
            group_data = data.get(self.group_data_set)

            if not group_data.get(chat_id, None) or not group_data[chat_id].get(wanted_user.id, None):
                bot.send_message(
                    chat_id=chat_id,
                    text='{wanted_user} was never warned.'.format(
                        wanted_user=get_user_link(wanted_user)),
                    parse_mode=ParseMode.MARKDOWN)
                return

            group_data[chat_id][wanted_user.id] = 0
            data.save(self.group_data_set, group_data)
            bot.send_message(
                chat_id=chat_id,
                text='{from_user} removed {wanted_user} warnings.'.format(
                    from_user=get_user_link(from_user),
                    wanted_user=get_user_link(wanted_user)),
                parse_mode=ParseMode.MARKDOWN)

    def delete(self, bot: Bot, update: Update):
        """Delete a post from a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if self.is_allowed(bot, update):
            if update.message.reply_to_message is None:
                return
            chat_id = update.message.chat_id
            wanted_user = update.message.reply_to_message.from_user

            bot.delete_message(chat_id=chat_id, message_id=update.message.reply_to_message.message_id)
            self.warn(bot, update, wanted_user)

    def rules_define(self, bot: Bot, update: Update):
        """Define new rules for a group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.is_admin(bot, update) or not self.in_group(update):
            return

        split_text = update.message.text.split(' ', 1)
        if len(split_text) < 2:
            update.message.reply_text('You forgot to give me the rules.')
            return
        elif len(split_text[1]) > 4000:
            update.message.reply_text('Rules must be less than 4000 characters.')
            return

        text = split_text[1]
        chat_id = update.message.chat_id
        from_user = update.message.from_user

        group_data = data.get(self.group_data_set)

        if not group_data.get(chat_id, None):
            group_data[chat_id] = {}

        group_data[chat_id]['rules'] = text
        data.save(self.group_data_set, group_data)

        bot.send_message(
            chat_id=chat_id,
            text='{user} has set new /rules.'.format(user=get_user_link(from_user)),
            parse_mode=ParseMode.MARKDOWN
        )

    def rules_remove(self, bot: Bot, update: Update):
        """Remove rules for a group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.is_admin(bot, update) or not self.in_group(update):
            return

        chat_id = update.message.chat_id
        from_user = update.message.from_user
        group_data = data.get(self.group_data_set)

        if not group_data.get(chat_id, None) or not group_data[chat_id].get('rules', None):
            bot.send_message(
                chat_id=chat_id,
                text='This group has no rules defined, use /rules_define to add them.')
            return

        group_data[chat_id]['rules'] = ''
        data.save(self.group_data_set, group_data)
        bot.send_message(
            chat_id=chat_id,
            text='{user} has set removed the groups rules.'.format(
                user=get_user_link(from_user)
            ),
            parse_mode=ParseMode.MARKDOWN
        )

    def rules(self, bot: Bot, update: Update):
        """Show the defined group rules

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.in_group(update):
            return

        chat_id = update.message.chat_id
        group_data = data.get(self.group_data_set)

        if not group_data.get(chat_id, None) or not group_data[chat_id].get('rules', None):
            bot.send_message(
                chat_id=chat_id,
                text='This group has no rules defined, use /rules_define to add them.')
            return

        bot.send_message(
            chat_id=chat_id,
            text=group_data[chat_id]['rules'],
            parse_mode=ParseMode.MARKDOWN)


group_manager = GroupManager()
