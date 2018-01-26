import re
# noinspection PyUnresolvedReferences
from math import *

import logzero
from telegram import Bot, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async

from xenian_bot.settings import LOG_LEVEL
from . import BaseCommand

__all__ = ['calculator']

logger = logzero.setup_logger(name=__name__, level=LOG_LEVEL)


class Calculator(BaseCommand):
    """A small class which acts as an calculator

    Attributes:
        safe_list (:obj:`list`): A list with allowed commands inside eval
        safe_dict (:obj:`dict`): A dict generated from the :obj:`Calculator.safe_list` where the key is the name of a
            function and the value is the actual function. This dict is passed to the eval and acts as the locals()
            This is to ensure that eval is not evil.
    """
    safe_list = [
        'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp',
        'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'
    ]
    safe_dict = dict([(k, globals().get(k, None)) for k in safe_list])

    def __init__(self):
        self.commands = [
            {
                'title': 'Calculator',
                'description': 'Solve equations you send me, to get a full list of supported math functions use /maths '
                               '(PRIVATE CHAT ONLY)',
                'command': self.calcualate,
                'handler': MessageHandler,
                'options': {'filters': Filters.text & ~ Filters.group},
            },
            {
                'title': 'Math Functions',
                'description': 'Show all available math functions',
                'command': self.maths,
            },
            {
                'title': 'Calculate',
                'description': 'Solve an equation you send me, all math functions can be seen with /maths',
                'args': 'EQUATION',
                'command_name': 'calc',
                'options': {'pass_args': True},
                'command': self.calcualate_command,
            },
        ]

        super(Calculator, self).__init__()

    @run_async
    def calcualate(self, bot: Bot, update: Update, equation: str = None):
        """Calculate

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            equation (:obj:`str`): Give an equation to solve and send the user or try to use the sent text
        """
        equation = equation or update.message.text
        equation = re.sub('["\']', '', equation)
        equation = re.sub('(true|false)', '', equation, flags=re.IGNORECASE)
        message = ''
        try:
            result = eval(equation, {"__builtins__": None}, self.safe_dict)
            reply_template = '{message}\n`{equation} = {result}`'
            try:
                result = float(result)
            except OverflowError:
                message = 'Result could not be shortened, shown in long format:'
            try:
                reply = reply_template.format(
                    message=message,
                    equation=equation,
                    result=result
                )
                update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
            except BadRequest:
                update.message.reply_text('Result was too long (max. 4096 characters) for Telegram.')
        except (SyntaxError, TypeError) as e:
            pass

    def calcualate_command(self, bot: Bot, update: Update, args: list = None):
        """Calculate

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`List`): User shall pass a equation
        """
        equation = ' '.join(args).strip()
        if equation:
            self.calcualate(bot, update, equation)
        else:
            update.message.reply_text('You have to give me an equation')

    @run_async
    def maths(self, bot: Bot, update: Update):
        """Show available Maths Functions

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        math_list = '**Available Math Functions**\n'
        func_pattern = re.compile('^.*\)')

        for math_func in self.safe_dict.values():
            doc = math_func.__doc__
            func_name = func_pattern.findall(doc)[0]

            for char in ['*', '_', '~']:
                doc = doc.replace(char, '\{}'.format(char))

            doc = doc.replace(func_name, '`{}`'.format(func_name), 1)

            math_list += '\n{seperator}\n{description}'.format(
                seperator='-' * 20,
                description=doc
            )

        update.message.reply_text(math_list, parse_mode=ParseMode.MARKDOWN)


calculator = Calculator()
