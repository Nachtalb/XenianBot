import re
from random import randint

from telegram import Bot, Update

from xenian.bot.commands import BaseCommand

__all__ = ['roll']


class Roll(BaseCommand):
    """Roll a dice
    """

    group = 'Misc'

    def __init__(self):
        self.commands = [
            {
                'title': 'Rolling Dice',
                'description': 'Roll a number between 0 and 6 or give me another range',
                'args': ['min', 'max'],
                'options': {'pass_args': True},
                'command': self.roll
            }
        ]

        super(Roll, self).__init__()

    def roll(self, bot: Bot, update: Update, args: list = None):
        """Roll a number between 0 and 6 or a specific range

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        min_ = int(args[0]) if len(args) >= 1 and bool(re.match('^\d+$', args[0])) else 1
        max_ = int(args[1]) if len(args) >= 2 and bool(re.match('^\d+$', args[1])) else 6
        update.message.reply_text(('{roll:0>' + str(len(str(max_))) + '}').format(roll=randint(min_, max_)))


roll = Roll()
