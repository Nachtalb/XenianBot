import logging
from typing import Callable, Dict, List

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, Filters, MessageHandler

from xenian.bot.models import Button, TgChat, TgMessage, TgUser
from xenian.bot.settings import LOG_LEVEL
from xenian.bot.utils.telegram import wants_update_bot

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
        >>> from xenian.bot.commands.base import BaseCommand
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
        self.bot = None
        self.update = None
        self.user = None
        self.message = None
        self.chat = None

        self.tg_chat = None
        self.tg_user = None
        self.tg_message = None

        BaseCommand.all_commands.append(self)

        self.normalize_commands()

    def on_call_wrapper(self, method: callable):
        def wrapper(bot: Bot, update: Update, *args, **kwargs):
            self.on_call(bot, update)
            if wants_update_bot(method):
                method(bot=bot, update=update, *args, **kwargs)
            else:
                method(*args, **kwargs)

        return wrapper

    def on_call(self, bot: Bot, update: Update):
        self.bot = bot
        self.update = update

        self.user = update.effective_user
        self.message = update.effective_message
        self.chat = update.effective_chat

        if self.user:
            self.tg_user = TgUser.from_object(self.user)
            self.tg_user.save()
        if self.chat:
            self.tg_chat = TgChat.from_object(self.chat)
            self.tg_chat.save()
        if self.message:
            self.tg_message = TgMessage.from_object(self.message)
            self.tg_message.save()

    @classmethod
    def bot_started(cls, bot: Bot):
        for command_class in BaseCommand.all_commands:
            if hasattr(command_class, 'start_hook'):
                command_class.start_hook(bot)

    def normalize_commands(self):
        """Normalize commands faults, add defaults and add them to :obj:`BaseCommand.all_commands`
        """
        updated_commands = []
        alias_commands = []
        for command in self.commands:
            if isinstance(command.get('alias', None), str):
                alias_commands.append(command)
                continue

            command = {
                'title': command.get('title', None) or command['command'].__name__.capitalize().replace('_', ' '),
                'description': command.get('description', ''),
                'command_name': command.get('command_name', command['command'].__name__),
                'command': self.on_call_wrapper(command['command']),
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

            new_command = self.copy_command(real_command)
            new_command['options']['command'] = alias_command['command_name']
            for key, value in alias_command.items():
                if key in ['title', 'description', 'hidden', 'group', 'command_name']:
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

    def copy_command(self, command: Dict) -> Dict:
        """Copy command to a new dict

        Do not use a single Dict.copy because the dicts are multidimensional and .copy i only onedimensional.
        Do not use deepcopy because it copies functions to a new object which leads to errors

        Instead we use copy the dict with its normal copy function and then iterate over the dict and repeat this for
        every sub dict.

        Args:
            command (:obj:`Dict`): A command dict to copy

        Returns:
            :obj:`Dict`: The copied dict

        """
        new_command = command.copy()
        for key, value in command.items():
            if isinstance(value, Dict):
                new_command[key] = self.copy_command(value)
        return new_command

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

    def not_implemented(self, bot: Bot, update: Update, *args, **kwargs):
        """

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            *args (:obj:`list`, optional): Unused other arguments but preserved for compatibility
            **kwargs (:obj:`dict`, optional): Unused keyword arguments but preserved for compatibility
        """
        if LOG_LEVEL <= logging.DEBUG:
            update.message.reply_text('This command was not implemented by the admin.',
                                      reply_to_message_id=update.message.message_id)

    def create_button(self, text: str, callback: str or Callable = None, data: Dict = None,
                      url: str = None, prefix: str = None, confirmation_requred: bool = False,
                      abort_callback: str = None) -> Button:
        prefix = prefix or 'button'

        if isinstance(callback, Callable):
            callback = callback.__name__
        if isinstance(abort_callback, Callable):
            abort_callback = abort_callback.__name__

        button = Button(text=text, callback=callback, data=data or {}, url=url or '', prefix=prefix,
                        confirmation_requred=confirmation_requred, abort_callback=abort_callback)
        button.save()
        return button

    def convert_button(self, button: Button) -> InlineKeyboardButton:
        if button.url:
            return InlineKeyboardButton(text=button.text, url=button.url)

        return InlineKeyboardButton(text=button.text, callback_data=button.callback_data())

    def answer_convert_button(self, button: Button, answer_text: str, answer: bool) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=answer_text, callback_data=button.callback_data(answer))

    def convert_buttons(self, buttons: List[List[Button or InlineKeyboardButton]]) -> InlineKeyboardMarkup:
        real_buttons = []
        for row in buttons:
            new_row = []
            for button in row:
                if isinstance(button, InlineKeyboardButton):
                    new_row.append(button)
                    continue

                new_row.append(self.convert_button(button))
            real_buttons.append(new_row)
        return InlineKeyboardMarkup(real_buttons)

    def get_button(self, button_id: str) -> Button:
        prefix, button_id = button_id.split(':', 1)
        if ':' in button_id:
            button_id, _ = button_id.split(':', 1)
        return Button.objects(id=button_id, prefix=prefix).first()

    def get_real_callback(self, button: Button, abort_callback: bool = False) -> Callable:
        if abort_callback:
            return getattr(self, button.abort_callback, None)
        else:
            return getattr(self, button.callback, None)

    def button_dispatcher(self):
        callback_data = self.update.callback_query.data
        button = self.get_button(callback_data)

        if not button:
            self.message.delete()
            return

        answer = button.extract_answer(callback_data)
        method = self.get_real_callback(button)
        if button.confirmation_requred and answer is None:
            buttons = self.convert_buttons([[
                self.answer_convert_button(button, 'Yes', True),
                self.answer_convert_button(button, 'No', False),
            ]])
            self.message.edit_text(text='Are you sure?', reply_markup=buttons)
            return
        elif button.confirmation_requred and isinstance(answer, bool) and not answer:
            method = self.get_real_callback(button, abort_callback=True)
            button.delete()
        else:
            button.delete()

        method(button=button)
