from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler
from telegram.parsemode import ParseMode

from xenian.bot.settings import ADMINS, SUPPORTER
from xenian.bot.utils import data, get_user_link, render_template
from .base import BaseCommand

__all__ = ['builtins']


class Builtins(BaseCommand):
    """A set of base commands which every bot should have
    """

    Group = 'Bot Helpers'
    data_set_name = 'builtins'

    def __init__(self):
        self.commands = [
            {'command': self.start, 'description': 'Initialize the bot'},
            {'command': self.commands, 'description': 'Show all available commands', 'options': {'pass_args': True}},
            {'command': self.support, 'description': 'Contact bot maintainer for support of any kind'},
            {'command': self.register, 'description': 'Register the chat_id for admins and supporters', 'hidden': True},
            {
                'command': self.contribute,
                'description': 'Send the supporters and admins a request of any kind',
                'args': ['text']
            },
            {
                'command': self.error,
                'description': 'If you have found an error please use this command.',
                'args': ['text']
            },
        ]

        super(Builtins, self).__init__()

    def start(self, bot: Bot, update: Update):
        """Initialize the bot

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text(render_template('start.html.mako'), parse_mode=ParseMode.HTML)

    def commands(self, bot: Bot, update: Update, args: list = None):
        """Generate and show list of available commands

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        direct_commands = {}
        indirect_commands = {}
        for command_class in BaseCommand.all_commands:
            group_name = command_class.group

            direct_commands.setdefault(group_name, [])
            indirect_commands.setdefault(group_name, [])

            # Direct commands (CommandHandler)
            for command in [cmd for cmd in command_class.commands
                            if cmd['handler'] == CommandHandler and not cmd['hidden']]:
                direct_commands[group_name].append({
                    'command': command['command_name'],
                    'args': command['args'],
                    'title': command['title'],
                    'description': command['description'],
                })
            if not direct_commands[group_name]:
                del direct_commands[group_name]

            # Indirect commands (MessageHandler)
            for command in [cmd for cmd in command_class.commands
                            if cmd['handler'] == MessageHandler and not cmd['hidden']]:
                indirect_commands[group_name].append({
                    'title': command['title'],
                    'description': command['description'],
                })

            if not indirect_commands[group_name]:
                del indirect_commands[group_name]
        if 'raw' in args:
            reply = render_template('commands_raw.html.mako', direct_commands=direct_commands)
        elif 'rst' in args:
            reply = render_template('commands_rst.mako',
                                    direct_commands=direct_commands,
                                    indirect_commands=indirect_commands)
            print(reply)
            update.message.reply_text(reply)
            return
        else:
            reply = render_template('commands.html.mako',
                                    direct_commands=direct_commands,
                                    indirect_commands=indirect_commands)
        update.message.reply_text(reply, parse_mode=ParseMode.HTML)

    def support(self, bot: Bot, update: Update):
        """Contact bot maintainer for support of any kind

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text(
            'If you need any help do not hesitate to contact me via "/contribute YOUR_MESSAGE", if you have found an '
            'error please use "/error ERROR_DESCRIPTION".\n\nIf you like this bot you can give me rating here: '
            'https://telegram.me/storebot?start=xenianbot'.format(SUPPORTER[0]))

    def contribute(self, bot: Bot, update: Update):
        """User can use /contribute to let all supporter / admin know something

        This should be used for feature requests or questions

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        split_text = update.message.text.split(' ', 1)
        if len(split_text) < 2:
            update.message.reply_text('Please describe your request with "/contribute YOUR_DESCRIPTION"')
            return

        text = split_text[1]
        admin_text = 'Contribution form {user}: {text}'.format(
            user=get_user_link(update.message.from_user),
            text=text,
            parse_mode=ParseMode.MARKDOWN
        )

        self.write_admins(bot, admin_text)
        self.write_supporters(bot, admin_text)

        update.message.reply_text('I forwarded your request to the admins and supporters.')

    def error(self, bot: Bot, update: Update):
        """User can use /error to let all supporter / admin know about a bug or something else which has gone wrong

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        split_text = update.message.text.split(' ', 1)
        if len(split_text) < 2:
            update.message.reply_text('Please describe your issue with "/error YOUR_DESCRIPTION"')
            return

        text = split_text[1]
        admin_text = 'Error form {user}: {text}'.format(
            user=get_user_link(update.message.from_user),
            text=text,
            parse_mode=ParseMode.MARKDOWN
        )

        self.write_admins(bot, admin_text)
        self.write_supporters(bot, admin_text)

        update.message.reply_text('I forwarded your request to the admins and supporters.')

    def write_admins(self, bot: Bot, text: str):
        """Send a message to all admins

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            text (:obj:`str`): Message to tell the admins
        """
        builtin_data = data.get(self.data_set_name)
        if builtin_data.get('admin_chat_ids', None):
            for name in builtin_data['admin_chat_ids']:
                bot.send_message(chat_id=name, text=text)

    def write_supporters(self, bot: Bot, text: str):
        """Send a message to all supporters

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            text (:obj:`str`): Message to tell the supporters
        """
        builtin_data = data.get(self.data_set_name)
        if builtin_data.get('supporter_chat_ids', None):
            for chat_id in builtin_data['supporter_chat_ids']:
                bot.send_message(chat_id=chat_id, text=text)

    def register(self, bot: Bot, update: Update):
        """Register the chat_id for admins and supporters

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        user = update.message.from_user
        chat_id = update.message.chat_id
        builtin_data = data.get(self.data_set_name)

        if '@{}'.format(user.username) in ADMINS:
            if not builtin_data.get('admin_chat_ids', None):
                builtin_data['admin_chat_ids'] = {}
            builtin_data['admin_chat_ids'][chat_id] = user.to_dict()

        if '@{}'.format(user.username) in SUPPORTER:
            if not builtin_data.get('supporter_chat_ids', None):
                builtin_data['supporter_chat_ids'] = {}
            builtin_data['supporter_chat_ids'][chat_id] = user.to_dict()

        data.save(self.data_set_name, builtin_data)


builtins = Builtins()
