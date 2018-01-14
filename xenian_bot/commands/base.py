from telegram import Bot, Update
from telegram.ext import CommandHandler

__all__ = ['BaseCommand']


class BaseCommand:
    """
    Attributes:
        all_commands (:class:`list`): A list of all initialized commands
        short (:obj:`str`): The command as it is used in Telegram with /some_command
        name (:class:`str`): A short title / name for the command
        description (:obj:`str`): What the command does
        handler (:obj:`class`): What handler the command has
        options (:obj:`dict`): Options for the handler
        hidden (:obj:`bool`): To hide the command from command listing
        args (:obj:`str`): Description of args, eg. for a command like "/add_human Nick 20 male" write "NAME AGE GENDER"
    """
    all_commands = []

    command_name = ''
    title = ''
    description = ''
    handler = CommandHandler
    options = {}
    hidden = False
    args = ''

    def __init__(self):
        """Initialize the command

        Notes:
            If you implement this method in your own command you must call super init or otherwise the command will not
            be found in the all_commands list.
        """
        BaseCommand.all_commands.append(self)

        self.command_name = self.command_name or self.__class__.__name__.lower()
        self.title = self.title or self.__class__.__name__.capitalize()

        self.options = {
            'command': self.command_name,
            'callback': self.command
        }

    def command(self, bot: Bot, update: Update):
        """The actual command

        This is the actual command in which you will be placing your code.

        Notes:
            If you want the command to be run asynchronously, give the command the
            :obj:`telegram.ext.dispatcher.run_async` decorator

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of arguments given by the user

        Raises:
            :obj:`NotImplementedError`: Whenever you do not implement the command of course
        """
        raise NotImplementedError()
