from random import randint

from telegram import Bot, Update

from xenian_bot.commands import BaseCommand

__all__ = ['rawl']


class Rawl(BaseCommand):
    def __init__(self):
        self.commands = [
            {
                'title': 'Rawling',
                'description': 'Rawl a number between 0 and 10000',
                'command': self.rawl
            }
        ]

        super(Rawl, self).__init__()

    def rawl(self, bot: Bot, update: Update):
        """Rawl a number between 0 and 10000

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of sent arguments
        """
        update.message.reply_text('{rawl:0>5}'.format(rawl=randint(0, 10000)))


rawl = Rawl()
