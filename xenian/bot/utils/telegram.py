import inspect
from functools import wraps
from typing import Callable

from telegram import Bot, Update, User
from telegram.error import NetworkError, TimedOut

from . import MWT

__all__ = ['get_self', 'get_user_link', 'get_option_from_string', 'user_is_admin_of_group', 'keep_message_args',
           'wants_update_bot']


@MWT(timeout=60 * 60)
def get_self(bot: Bot) -> User:
    """Get User object of this bot

    Args:
        bot (:obj:`Bot`): Telegram Api Bot Object

    Returns:
        :obj:`User`: The user object of this bot
    """
    return bot.get_me()


def get_user_link(user: User) -> str:
    """Get the link to a user

    Either the @Username or [First Name](tg://user?id=123456)

    Args:
        user (:obj:`telegram.user.User`): A Telegram User Object

    Returns:
        :obj:`str`: The link to a user
    """
    if user.username:
        return '@{}'.format(user.username)
    else:
        return '[{}](tg://user?id={})'.format(user.first_name, user.id)


def get_option_from_string(option_short: str, string: str) -> tuple:
    """Extract option from a string

    Examples:
        >>> string = 'This is some user message -echo_it Yes'
        >>> result = get_option_from_string('echo_it', string)
        >>> print(result)
        >>> # ('Yes', 'This is some user message')

        >>> string = 'This is some user message'
        >>> result = get_option_from_string('echo_it', string)
        >>> print(result)
        >>> # (None, None)

    Args:
        option_short (:obj:`str`): The name of the option
        string (:obj:`str`): Whole string from where to extract from

    Returns:
        :obj:`tuple`: A Tuple of the found option and the string without the option or a tuple of two None's
    """
    splitted_text = string.split(' ')
    option_short = option_short if option_short.startswith('-') else '-' + option_short
    if option_short in splitted_text:
        in_list_position = splitted_text.index(option_short)
        if len(splitted_text) > in_list_position + 1:
            option = splitted_text[in_list_position + 1]
            for index in range(2):
                del splitted_text[in_list_position]
            string = ' '.join(splitted_text)
            return option, string
    return None, None


def user_is_admin_of_group(chat, user):
    """Check if the given user is admin of the chat

    Attributes:
        chat (:obj:`Chat`): Telegram Chat Object
        user (:obj:`User`): Telegram User Object
    """
    if chat.all_members_are_administrators:
        return True

    for member in chat.get_administrators():
        if user == member.user:
            return True
    return False


def retry_command(retries: int = None, *args, notify_user=True, existing_update: Update = None,
                  **kwargs) -> Callable:
    """Decorater to retry a command if it raises :class:`telegram.error.TimedOut`

    Args:
        retries (:obj:`int`): How many times the command should be retried
        notify_user (:obj:`bool`): Try to notify user if TimedOut is still raised after given amount of retires
        existing_update (:obj:`telegram.update.Update`): Telegram Api Update Object if the decorated function is
            not a command

    Raises:
        (:class:`telegram.error.TimedOut`): If TimedOut is still raised after given amount of retires

    Returns:
        (:object:`Callable`): Wrapper function
    """
    func = None
    if isinstance(retries, Callable):
        func = retries
        retries = 3
    retries = retries or 3

    def wrapper(*args, **kwargs):
        error = None
        for try_ in range(retries):
            error = None
            try:
                return func(*args, **kwargs)
            except (TimedOut, NetworkError) as e:
                if isinstance(e, TimedOut) or (
                        isinstance(e, NetworkError) and 'The write operation timed out' in e.message):
                    error = e
        else:
            if notify_user and existing_update or (len(args) > 1 and getattr(args[1], 'message', None)):
                update = existing_update or args[1]
                update.message.reply_text(text='Command failed at some point after multiple retries. '
                                               'Try again later or contact an admin /support.',
                                          reply_to_message_id=update.message.message_id)
            if error:
                raise error

    if func:
        return wrapper

    return wraps(wrapper)


def keep_message_args(func):
    """This decorator tells the bot to send the bot and update to the given function.

    This decorator must be on top of all other decorators to work
    """

    def wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return wrapper


def wants_update_bot(method: Callable) -> bool:
    signature = inspect.signature(method)
    if 'bot' in signature.parameters and 'update' in signature.parameters:
        return True
    return method.__qualname__.startswith('keep_message_args')
