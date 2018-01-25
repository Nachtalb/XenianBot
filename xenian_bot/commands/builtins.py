from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler
from telegram.parsemode import ParseMode

from xenian_bot.settings import SUPPORTER
from .base import BaseCommand

__all__ = ['builtins']


class Builtins(BaseCommand):
    """A set of base commands which every bot should have
    """

    def __init__(self):
        self.commands = [
            {'command': self.start, 'description': 'Initialize the bot'},
            {'command': self.commands, 'description': 'Show all available commands'},
            {'command': self.support, 'description': 'Contact bot maintainer for support of any kind'}
        ]

        super(Builtins, self).__init__()

    def start(self, bot: Bot, update: Update):
        """Initialize the bot

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        reply = ('Hello and welcome to me, **@XenianBot**\n\nI am a personal assistant which can do various tasks for '
                 'you. For example, I can do reverse image searches directly here in Telegram. To see my full '
                 'capability, use /commands.\n\nIf you like this bot you can give me a rating here: '
                 'https://telegram.me/storebot?start=xenianbot')
        update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    def commands(self, bot: Bot, update: Update):
        """Generate and show list of available commands

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        command_lists = []

        direct_commands = ''
        for command_class in BaseCommand.all_commands:
            for command in [cmd for cmd in command_class.commands
                            if cmd['handler'] == CommandHandler and not cmd['hidden']]:
                direct_commands += '/{command_name}{args} - {title}: {description}\n'.format(
                    command_name=command['command_name'],
                    args='%s' % ' ' + command['args'] if command['args'] else '',
                    title=command['title'],
                    description=command['description']
                )
        if direct_commands:
            direct_commands = 'List of direct commands:\n' + direct_commands
            command_lists.append(direct_commands)

        indirect_commands = ''
        for command_class in BaseCommand.all_commands:
            for command in [cmd for cmd in command_class.commands
                            if cmd['handler'] == MessageHandler and not cmd['hidden']]:
                indirect_commands += '- {title}: {description}\n'.format(
                    title=command['title'],
                    description=command['description']
                )
        if indirect_commands:
            indirect_commands = 'List of indirect commands:\n' + indirect_commands
            command_lists.append(indirect_commands)

        reply = ''
        for command_list in command_lists:
            reply += '\n\n' + command_list
        reply.strip()

        update.message.reply_text(reply)

    def support(self, bot: Bot, update: Update):
        """Contact bot maintainer for support of any kind

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text(
            'If you need any help do not hesitate to contact me via {}.\n\nIf you like this bot you can give me rating '
            'here: https://telegram.me/storebot?start=xenianbot'.format(SUPPORTER[0]))


builtins = Builtins()
