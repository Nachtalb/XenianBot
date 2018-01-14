from telegram import Bot, Update
from telegram.ext import MessageHandler, Filters
from telegram.parsemode import ParseMode


from .base import BaseCommand

__all__ = ['start', 'commands', 'unknown']


class Start(BaseCommand):
    description = 'Initialize the bot'

    def command(self, bot: Bot, update: Update):
        """Initialize the bot

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        reply = ('Hello and welcome to me, **@XenianBot**\n\nI am a personal assistant which can do various tasks for '
                 'you. For example, I can do reverse image searches directly here in Telegram. To see my full '
                 'capability, use /commands.')
        update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


start = Start()


class Commands(BaseCommand):
    description = 'Show all available commands'

    def command(self, bot: Bot, update: Update):
        """Generate and show list of available commands

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        reply = 'List of available commands:\n'

        for command in BaseCommand.all_commands:
            if command.hidden:
                continue
            reply += '{title} \[/{command_name}{args}]: {description}\n'.format(
                command_name=command.command_name,
                args=' %s' % command.args if command.args else '',
                title=command.title,
                description=command.description
            )
        update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


commands = Commands()


class Unknown(BaseCommand):
    description = "I am called when someone tries a command that does not exist"
    handler = MessageHandler
    hidden = True

    def __init__(self):
        super(Unknown, self).__init__()
        self.options = {'filters': Filters.command, 'callback': self.command}

    def command(self, bot: Bot, update: Update):
        """Send a error message to the client if the entered command did not work.

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text("Sorry, I didn't understand that command.")


unknown = Unknown()
