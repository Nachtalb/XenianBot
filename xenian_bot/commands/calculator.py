import re
# noinspection PyUnresolvedReferences
from math import *

from telegram import Bot, ParseMode, Update
from telegram.ext import Filters, MessageHandler

from . import BaseCommand

__all__ = ['calculator']


class Calculator(BaseCommand):
    safe_list = [
        'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp',
        'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh'
    ]
    safe_dict = dict([(k, globals().get(k, None)) for k in safe_list])

    def __init__(self):
        self.commands = [
            {
                'title': 'Calculator',
                'description': 'Solve equations you send me, to get a full list of supported math functions use /maths',
                'command': self.calcualate,
                'handler': MessageHandler,
                'options': {'filters': Filters.text},
            },
            {
                'title': 'Math Functions',
                'description': 'Show all available math functions',
                'command': self.maths,
            },
        ]

        super(Calculator, self).__init__()

    def calcualate(self, bot: Bot, update: Update):
        """Calculate

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        equation = update.message.text
        try:
            result = eval(equation, {"__builtins__": None}, self.safe_dict)
            update.message.reply_text('`{} = {}`'.format(equation, result), parse_mode=ParseMode.MARKDOWN)
        except (SyntaxError, TypeError) as e:
            pass

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
