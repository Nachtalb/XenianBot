import datetime

from telegram import Bot, ParseMode, Update, User
from telegram.ext import Filters

import xenian.bot
from xenian.bot.commands import BaseCommand, filters
from xenian.bot.utils import get_user_link

__all__ = ['group_manager']


class GroupManager(BaseCommand):
    """Roll a dice
    """

    group = 'Group Management'

    def __init__(self):
        self.commands = [
            {
                'title': 'Ban',
                'description': 'Ban a user. Reply to one of his messages with this command (Group Only)',
                'command': self.ban,
                'options': {
                    'filters': (
                            Filters.group
                            & ~ filters.all_admin_group
                            & ~ filters.reply_user_group_admin
                            & filters.bot_group_admin
                            & filters.user_group_admin
                    )
                },
            },
            {
                'title': 'Strike',
                'description': 'Warn a user, after 3 warnings he get banned. Reply to one of his messages with this '
                               'command (Group Only)',
                'command': self.warn,
                'options': {
                    'filters': (
                            Filters.group
                            & ~ filters.all_admin_group
                            & ~ filters.reply_user_group_admin
                            & filters.bot_group_admin
                            & filters.user_group_admin
                    )
                },
            },
            {
                'title': 'Kick',
                'description': 'Kick a user for 10 min or give a specific amount of time (in min) between 30sec '
                               '(0.5 min) and 366 days (527040 min). Reply to one of his messages with this command '
                               '(Group Only)',
                'args': ['time'],
                'command': self.kick,
                'options': {
                    'pass_args': True,
                    'filters': (
                            Filters.group
                            & ~ filters.all_admin_group
                            & ~ filters.reply_user_group_admin
                            & filters.bot_group_admin
                            & filters.user_group_admin
                    )
                },
            },
            {
                'title': 'Delete and Warn',
                'description': 'Delete a message from a user and warn them. Reply to one of his messages with this '
                               'command (Group Only)',
                'command': self.delete,
                'options': {
                    'filters': (
                            Filters.group
                            & ~ filters.all_admin_group
                            & ~ filters.reply_user_group_admin
                            & filters.bot_group_admin
                            & filters.user_group_admin
                    )
                },
            },
            {
                'title': 'Remove Warnings',
                'description': 'Remove all warnings from a User. Reply to one of his messages with this command '
                               '(Group Only)',
                'command': self.unwarn,
                'options': {
                    'filters': (
                            Filters.group
                            & ~ filters.all_admin_group
                            & ~ filters.reply_user_group_admin
                            & filters.bot_group_admin
                            & filters.user_group_admin
                    )
                },
            },
            {
                'title': 'Rules',
                'description': 'Show rules for this group (Group Only)',
                'command': self.rules,
                'options': {'filters': Filters.group},
            },
            {
                'title': 'Define Rules',
                'description': 'Define rules for this group (Group Only)',
                'args': ['text'],
                'command': self.rules_define,
                'options': {
                    'filters': (
                            Filters.group
                            & filters.user_group_admin
                    )
                },
            },
            {
                'title': 'Remove Rules',
                'description': 'Remove rules for this group (Group Only)',
                'command': self.rules_remove,
                'options': {
                    'filters': (
                            Filters.group
                            & filters.user_group_admin
                    )
                },
            }
        ]

        super(GroupManager, self).__init__()

    def kick(self, bot: Bot, update: Update, args: list = None):
        """Kick a user for 30 sec or a specific amount of time

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): Time in min
        """
        if self.message.reply_to_message is None:
            self.message.reply_text('You have to reply to a message from this user to kick him.')
            return

        wanted_user = self.message.reply_to_message.from_user

        time = 10
        if args:
            try:
                time = float(args[0])
                if not 0.5 <= time <= 527040:
                    self.message.reply_text('Time must be between 30 sec (0.5 min) and 366 days (527040 min).')
                    return
            except ValueError:
                self.message.reply_text('You have to give me the time in min like `/kick 30`')
                return

        now = datetime.datetime.now()
        kick_until = now - datetime.timedelta(minutes=time)

        self.bot.kick_chat_member(chat_id=self.chat.id, user_id=wanted_user.id, until_date=kick_until)

        xenian.bot.job_queue.run_once(callback=(
            lambda bot, job: bot.send_message(
                self.chat.id,
                f'{get_user_link(wanted_user)} was kicked {time} min ago and can now join again',
                parse_mode=ParseMode.MARKDOWN)),
            when=10 * 60)

        self.message.reply_text(f'{get_user_link(wanted_user)} was kicked for {time} min by {get_user_link(self.user)}',
                                parse_mode=ParseMode.MARKDOWN)

    def ban(self, *args, wanted_user: User = None, **kwargs):
        """Ban a user
        """
        if self.message.reply_to_message is None and not wanted_user:
            self.message.reply_text('You have to reply to a message from this user to ban him.')
            return

        wanted_user = wanted_user or self.message.reply_to_message.from_user
        self.chat.group_warnings[wanted_user.id] = 3
        self.chat.group_warnings.save()

        self.bot.kick_chat_member(chat_id=self.chat.id, user_id=wanted_user.id, until_date=datetime.datetime.now())
        self.message.reply_text(text=f'{get_user_link(wanted_user)} was banned by {get_user_link(self.user)}',
                                parse_mode=ParseMode.MARKDOWN)

    def warn(self, bot: Bot, update: Update, wanted_user: User = None):
        """Strike a user

        After 3 strikes he is banned

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            wanted_user (:obj:`telegram.user.User`): Telegram User object of the user which should be warned
        """
        if self.message.reply_to_message is None:
            self.message.reply_text('You have to reply to a message from this user to warn him.')
            return

        wanted_user = wanted_user or self.message.reply_to_message.from_user

        self.chat.group_warnings[wanted_user.id] = self.chat.group_warnings.get(wanted_user.id, 0) + 1
        self.chat.save()

        if self.chat.group_warnings[wanted_user.id] > 2:
            self.ban(wanted_user=wanted_user)
            return
        self.message.reply_text(f'{get_user_link(wanted_user)} was warned.\nUser has now '
                                f'`{self.chat.group_warnings[wanted_user.id]}` warnings. Users with 3 warnings get '
                                f'banned automatically.', parse_mode=ParseMode.MARKDOWN)
        return

    def unwarn(self, bot: Bot, update: Update, wanted_user: User = None):
        """Remove all warnings from a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            wanted_user (:obj:`telegram.user.User`): Telegram User object of the user which should be warned
        """
        if self.message.reply_to_message is None:
            self.message.reply_text('You have to reply to a message from a user to warn him.')
            return
        wanted_user = wanted_user or self.message.reply_to_message.from_user

        if wanted_user.id not in self.chat.group_warnings:
            self.message.reply_text(f'{get_user_link(wanted_user)} was never warned', parse_mode=ParseMode.MARKDOWN)
            return

        self.chat.group_warnings[wanted_user.id] = 0
        self.chat.save()
        self.message.reply_text(f'Warnings were removed from {get_user_link(wanted_user)}.')

    def delete(self, bot: Bot, update: Update):
        """Delete a post from a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if self.message.reply_to_message is None:
            return

        wanted_user = self.message.reply_to_message.from_user

        self.bot.delete_message(chat_id=self.chat.id, message_id=self.message.reply_to_message.message_id)
        self.bot.delete_message(chat_id=self.chat.id, message_id=self.message.message_id)
        self.warn(self.bot, self.update, wanted_user)

    def rules_define(self, bot: Bot, update: Update):
        """Define new rules for a group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        text = None
        if self.message.reply_to_message:
            text = self.message.reply_to_message.text
        else:
            split_text = self.message.text.split(' ', 1)
            if len(split_text) > 1:
                text = split_text[1]

        if not text:
            self.message.reply_text('You either have to reply to a message with text or give me some text. '
                                    'The rules accept markdown. ')
            return

        self.tg_chat.group_rules = text
        self.tg_chat.save()

        self.message.reply_text(text=f'{get_user_link(self.user)} has set new /rules.', parse_mode=ParseMode.MARKDOWN)

    def rules_remove(self, bot: Bot, update: Update):
        """Remove rules for a group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.tg_chat.group_rules:
            self.message.reply_text(text='This group has no rules defined, use /rules_define to add them.')
            return
        self.tg_chat.group_rules = ''
        self.tg_chat.save()
        self.message.reply_text(text=f'{get_user_link(self.user)} has set removed the groups rules.',
                                parse_mode=ParseMode.MARKDOWN)

    def rules(self, bot: Bot, update: Update):
        """Show the defined group rules

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.tg_chat.group_rules:
            self.message.reply_text('This group has no rules defined, use /rules_define to add them.')
            return

        self.message.reply_text(self.tg_chat.group_rules, parse_mode=ParseMode.MARKDOWN)


group_manager = GroupManager()
