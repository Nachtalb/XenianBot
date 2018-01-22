from random import randint

from telegram import Bot, Update

from . import BaseCommand

__all__ = ['decide']


class Decide(BaseCommand):
    """Decide command if you don't know any further
    """
    def __init__(self):
        self.commands = [{'description': 'Yes or No', 'command': self.decide}, ]

        super(Decide, self).__init__()

    def decide(self, bot: Bot, update: Update):
        """Decide

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Yes' if randint(0, 1) else 'No')


decide = Decide()
