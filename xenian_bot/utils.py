import json
import os
from codecs import open as copen

from emoji import emojize
from telegram import Bot, ParseMode


class Data:

    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(dir_path, 'data')
        os.makedirs(self.data_dir, exist_ok=True)

    def save(self, name: str, data: object):
        """Save object to json

        Args:
            name (:obj:`str`): Name of data object
            data (:obj:`object`): JSON serializable data object
        """
        name = os.path.splitext(os.path.basename(name))[0]
        path = os.path.join(self.data_dir, name + '.json')
        with copen(path, mode='w', encoding='utf-8') as data_file:
            json.dump(data, data_file, ensure_ascii=False, indent=4, sort_keys=True)

    def get(self, name: object) -> object:
        """Get data by name

        Args:
            name (:obj:`str`): Name of data object
        """
        name = os.path.splitext(os.path.basename(name))[0]
        path = os.path.join(self.data_dir, name + '.json')
        if not os.path.isfile(path):
            os.mknod(path, 0o644)
        with copen(path, encoding='utf-8') as data_file:
            content = data_file.read()
            content = content or '{}'
            return json.loads(content)


data = Data()


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


class TelegramProgressBar:
    """Create a progressbar for the Telegram user.

    Attributes:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        chat_id (:obj:`int`): Unique identifier of the chat with a user.
        full_amount (:obj:`int` or :obj:`float`): Total amount of items.
        step_size (:obj:`int` or :obj:`float`): On nth item send update message to user.
        line_width (:obj:`int`): With of progressbar in characters.
        pre_message (:obj:`str`): Message which comes a line above the Progressbar.
        se_message (:obj:`str`): Message which comes a line under the Progressbar.
        loaded_char (:obj:`str`): Character to be displayed as loaded in the progressbar.
        unloaded_char (:obj:`str`): Character to be displayed as not yet loaded in the progressbar.
        last_message (:obj:`telegram.message.Message`): Last message send from the progressbar.
        current_step (:obj:`int` or :obj:`float`): What number of step we are currently at.

    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        chat_id (:obj:`int`): Unique identifier of the chat with a user.
        full_amount (:obj:`int` or :obj:`float`): Total amount of items.
        step_size (:obj:`int` or :obj:`float`): On nth item send update message to user.
        line_width (:obj:`int`): With of progressbar in characters.
        pre_message (:obj:`str`): Message which comes a line above the Progressbar. Available placeholders are:
            {current} == current step number
            {total} == total step number
            {step_size} == step size
        se_message (:obj:`str`): Message which comes a line under the Progressbar. The same placeholders are available
            as in pre_message
        loaded_char (:obj:`str`): Character to be displayed as loaded in the progressbar, you can use emojis like so
            :cake: or :joy:
        unloaded_char (:obj:`str`): Character to be displayed as not yet loaded in the progressbar, you can use emojis
            like so :cake: or :joy:
    """
    last_message = None

    def __init__(self,
                 bot: Bot,
                 chat_id: int,
                 full_amount: int or float = None,
                 step_size: int or float = None,
                 line_width: int = None,
                 pre_message: str = None,
                 se_message: str = None,
                 loaded_char: str = None,
                 unloaded_char: str = None,
                 ):
        # Mandatory
        self.bot = bot
        self.chat_id = chat_id
        # Optional
        self.full_amount = full_amount or None
        self.step_size = step_size or 0
        self.line_width = line_width or 20
        self.pre_message = emojize(pre_message or '', use_aliases=True)
        self.se_message = emojize(se_message or '', use_aliases=True)
        self.loaded_char = emojize(loaded_char or '▉', use_aliases=True)
        self.unloaded_char = emojize(unloaded_char or '▒', use_aliases=True)

        self.current_step = 0

    def start(self,
              current_step: int or float= None,
              full_amount: int or float = None,
              line_width: int = None,
              pre_message: str = None,
              se_message: str = None,
              loaded_char: str = None,
              unloaded_char: str = None,
              ):
        """Show empty progressbar and initialize any new value.

        Args:
            current_step (:obj:`int` or :obj:`float`): Your current stop number. If left away it just increases by one.
            full_amount (:obj:`int` or :obj:`float`): Total amount of items. Set it here if not yet set in the beginning.
            line_width (:obj:`int`): With of progressbar in characters.
            pre_message (:obj:`str`): Message which comes a line above the Progressbar. Available placeholders are:
                {current} == current step number
                {total} == total step number
                {step_size} == step size
            se_message (:obj:`str`): Message which comes a line under the Progressbar. The same placeholders are
                available as in pre_message
            loaded_char (:obj:`str`): Character to be displayed as loaded in the progressbar, you can use emojis like so
                :cake: or :joy:
            unloaded_char (:obj:`str`): Character to be displayed as not yet loaded in the progressbar, you can use
                emojis like so :cake: or :joy:
        """
        self.current_step = current_step or self.current_step
        self.full_amount = full_amount or self.full_amount
        self.line_width = line_width or 20

        if pre_message:
            self.pre_message = emojize(pre_message, use_aliases=True)
        if se_message:
            self.se_message = emojize(se_message, use_aliases=True)
        if loaded_char:
            self.loaded_char = emojize(loaded_char, use_aliases=True)
        if unloaded_char:
            self.unloaded_char = emojize(unloaded_char, use_aliases=True)

        message = '{pre}{bar}{se}'.format(pre=self.pre_message + '\n' if self.pre_message else '',
                                          bar=self.unloaded_char * self.line_width,
                                          se='\n' + self.se_message if self.se_message else '')
        message = message.format(current=self.current_step, total=self.full_amount, step_size=self.step_size)
        self.last_message = self.bot.send_message(self.chat_id, message, parse_mode=ParseMode.MARKDOWN)

    def update(self,
               new_amount: int or float,
               new_full_amount: int or float = None,
               pre_message: str = None,
               se_message: str = None):
        """Update progress bar with its new amount.

        Args:
            new_amount (:obj:`int` or :obj:`float`): New amount
            new_full_amount (:obj:`int` or :obj:`float`): New full amount
            pre_message (:obj:`str`): Message which comes a line above the Progressbar. Available placeholders are:
                {current} == current step number
                {total} == total step number
                {step_size} == step size
            se_message (:obj:`str`): Message which comes a line under the Progressbar. The same placeholders are
                available as in pre_message
        """
        self.current_step = new_amount
        self.full_amount = self.full_amount or new_full_amount
        self.pre_message = pre_message or self.pre_message
        self.se_message = self.se_message or se_message
        self.print_message()

    def increase(self):
        """Increase current_step and send a message if item is nth step_size item.
        """
        self.current_step += 1
        if self.current_step % self.step_size != 0 and self.current_step != self.full_amount:
            return
        self.print_message()

    def print_message(self):
        """Print message to user
        """
        loaded_percentage = 1 / self.full_amount * self.current_step
        loaded_chars_amount = round(self.line_width * loaded_percentage)

        bar = (self.loaded_char * loaded_chars_amount) + (self.unloaded_char * (self.line_width - loaded_chars_amount))

        message = '{pre}{bar}{se}'.format(pre=self.pre_message + '\n' if self.pre_message else '',
                                          bar=bar,
                                          se='\n' + self.se_message if self.se_message else '')

        message = message.format(
            current=round(self.current_step, 2),
            total=round(self.full_amount, 2),
            step_size=self.step_size)
        if self.last_message:
            if self.last_message.text == message:
                return
            self.last_message = self.bot.edit_message_text(message, self.chat_id, self.last_message.message_id)
            return
        self.last_message = self.bot.send_message(self.chat_id, message, parse_mode=ParseMode.MARKDOWN)

    def remove(self):
        """Remove your progressbar from Telegram.
        """
        if self.last_message:
            self.bot.delete_message(self.chat_id, self.last_message.message_id)
