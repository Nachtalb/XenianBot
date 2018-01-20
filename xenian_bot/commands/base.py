from telegram import Bot, Update
from telegram.ext import CommandHandler

__all__ = ['BaseCommand']


class BaseCommand:
    """
    Attributes:
        all_commands (:class:`list`): A list of all initialized commands
        commands (:obj:`list`): A list of dictionary with the following keys:
            - title (:class:`str`): Title of the command, (if not set name of the function will be taken)
            - description (:class:`str`): A short description for the command
            - command_name (:class:`str`): A name for the command (if not set, the functions name will be taken)
            - command : The command function
            - handler : Handler for the command like :class:`CommandHandler` or :class:`MessageHandler`.
                Default (:class:`CommandHandler`)
            - options (:class:`dict`): A dictionary of options for the command.
                Default {'callback': command, 'command': command_name}
            - hidden (:class:`bool`): If the command is shown in the overview of `/commands`
            - args (:class:`str`): If the command has arguments define them here as text like: "USERNAME PASSWORD"
    """
    all_commands = []
    commands = []

    def __init__(self):
        """Initialize the command

        Notes:
            super(BaseCommand, self).__init__() has to be run after the self.commands setup
        """
        BaseCommand.all_commands.append(self)

        self.check_commands()

    def check_commands(self):
        updated_commands = []
        for command in self.commands:
            command = {
                'title': command.get('title', None) or command['command'].__name__.capitalize().replace('_', ' '),
                'description': command.get('description', ''),
                'command_name': command.get('command_name', None) or command['command'].__name__,
                'command': command['command'],
                'handler': command.get('handler', None) or CommandHandler,
                'options': command.get('options', None),
                'hidden': command.get('hidden', False),
                'args': command.get('args', None)
            }
            if command['options'] is None:
                command['options'] = {'callback': command['command'], 'command': command['command_name']}
            updated_commands.append(command)
        self.commands = updated_commands
