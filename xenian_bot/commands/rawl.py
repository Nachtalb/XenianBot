from random import randint

from telegram import Bot, Update

from xenian_bot.commands import BaseCommand

__all__ = ['rawl']


class Rawl(BaseCommand):
    title = 'Rawling'
    description = 'Rawl a number between 0 and 10000'

    def command(self, bot: Bot, update: Update, args: list = None):
        """Rawl a number between 0 and 10000

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of sent arguments
        """
        update.message.reply_text('{rawl:0>5}'.format(rawl=randint(0, 10000)))


rawl = Rawl()
