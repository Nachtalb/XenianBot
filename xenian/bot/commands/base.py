from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler, Filters, MessageHandler

__all__ = ['BaseCommand']


class BaseCommand:
    """Base of any command class

    This is the base which should be used for any new command class. A command class is a class containing one or more
    commands. For this to work the created command class must be called afterwards at least once. Like this an entry is
    made in this classes :obj:`BaseCommand.all_commands` for the new command class. This has the advantage that you can
    store all the data for your commands together in one place.

    Your commands are also automatically added to the Telegram Updater, as well as listed in the output of the /commands
    command from the :class:`xenian.bot.commands.builtins.Builtins` commands (unless you have hidden on true for your
    command).

    Examples:
        >>> from telegram.ext import Filters
        >>> from xenian.bot import BaseCommand
        >>>
        >>> class MyCommands(BaseCommand):
        >>>     def __init__(self):
        >>>         self.commands = [
        >>>             {
        >>>                 'title': 'Echo yourself',
        >>>                 'description': 'Return messages that you send me',
        >>>                 'command': self.echo,
        >>>                 'handler': MessageHandler,
        >>>                 'options': {'filters': Filters.text},
        >>>                 'group': 0
        >>>             }
        >>>         ]
        >>>
        >>>         super(MyCommands, self).__init__()
        >>>
        >>>     def echo(self, bot, update):
        >>>         update.message.reply_text(update.message.text)

    Attributes:
        all_commands (:class:`list` of :obj:`class`): A list of all initialized command classes
        commands (:obj:`list` of :obj:`dict`): A list of dictionary with the following keys:
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
            - group (:class:`int`): Which handler group the command should be in
        group (:class:`str`): The group name shown in the /commands message
    """
    all_commands = []
    commands = []
    group = 'Base Group'

    def __init__(self):
        """Initialize the command class

        Notes:
            super(BaseCommand, self).__init__() has to be run after the self.commands setup
        """
        BaseCommand.all_commands.append(self)

        self.normalize_commands()

    def normalize_commands(self):
        """Normalize commands faults, add defaults and add them to :obj:`BaseCommand.all_commands`
        """
        updated_commands = []
        alias_commands = []
        for command in self.commands:
            if isinstance(command.get('alias', None), str):
                alias_commands.append(command)
                continue
            if command['command'].__name__ == '<lambda>' and (not command.get('command_name') and
                                                              not command.get('handler') == CallbackQueryHandler):
                raise ValueError('If "command_wrapper" is used a "command_name" has to be defined or the handler must '
                                 'be an CallbackQueryHandeler!')

            command = {
                'title': command.get('title', None) or command['command'].__name__.capitalize().replace('_', ' '),
                'description': command.get('description', ''),
                'command_name': command.get('command_name', command['command'].__name__),
                'command': command['command'],
                'handler': command.get('handler', CommandHandler),
                'options': command.get('options', {}),
                'hidden': command.get('hidden', False),
                'args': command.get('args', []),
                'group': command.get('group', 0)
            }

            if command['handler'] == CommandHandler and command['options'].get('command', None) is None:
                command['options']['command'] = command['command_name']

            if command['handler'] == MessageHandler and command['options'].get('filters', None) is None:
                command['options']['filters'] = Filters.all

            # Set CallbackQueryHandler options if not yet set
            if command['options'].get('callback', None) is None:
                command['options']['callback'] = command['command']

            updated_commands.append(command)

        self.commands = updated_commands

        for alias_command in alias_commands:
            alias_name = alias_command['alias']

            real_command = self.get_command_by_name(alias_name)
            if not real_command:
                continue

            new_command = real_command.copy()
            for key, value in alias_command.items():
                if key in ['title', 'description', 'hidden', 'group']:
                    new_command[key] = value

            updated_commands.append(new_command)

        for command in updated_commands:
            try:
                int(command['group'])
            except ValueError:
                raise ValueError('Command group has to be an integer: command {}, given group {}'.format(
                    command['command_name'], command['group']
                ))

        self.commands = updated_commands

    def get_command_by_name(self, name: str) -> dict:
        """Returns a command form self.command with the given name

        Args:
            name (:obj:`str`): Name of the command

        Returns:
            (:obj:`dict` | :obj:`None`): The found command or :obj:`None` if no command was found
        """
        commands_found = list(filter(lambda command: command['command_name'] == name, self.commands))
        return commands_found[0] if commands_found else None

    def command_wrapper(self, method: callable, *args, **kwargs):
        return lambda bot, update, *args2, **kwargs2: method(bot, update, *args2, *args, **kwargs2, **kwargs)
