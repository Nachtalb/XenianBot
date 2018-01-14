import logging
import os
import sys
from threading import Thread

from telegram import Bot, TelegramError, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from .commands import BaseCommand
from .settings import TELEGRAM_API_TOKEN, ADMINS, MODE

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def error(bot: Bot, update: Update, error: TelegramError):
    """Log all errors from the telegram bot api

    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        update (:obj:`telegram.update.Update`): Telegram Api Update Object
        error (:obj:`telegram.error.TelegramError`): Telegram Api TelegramError Object
    """
    logger.warning('Update "%s" caused error "%s"' % (update, error))
    if update:
        update.message.reply_text('Whoops, there was an error. Please try again.')


def main():
    updater = Updater(TELEGRAM_API_TOKEN)
    dispatcher = updater.dispatcher

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one."""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(bot: Bot, update: Update):
        """Start the restarting process

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    dispatcher.add_handler(CommandHandler('restart', restart, filters=Filters.user(username=ADMINS)))

    for command in BaseCommand.all_commands:
        if not command.options:
            raise NotImplementedError('At least one option has to be given for a handler.')
        dispatcher.add_handler(command.handler(**command.options))

    # log all errors
    dispatcher.add_error_handler(error)

    if MODE['active'] == 'webhook':
        webhook = MODE['webhook']
        updater.start_webhook(listen=webhook['listen'], port=webhook['port'], url_path=webhook['url_path'])
        updater.bot.set_webhook(url=webhook['url'], certificate=webhook['certification'])
        logger.info('Starting webhook...')
    else:
        updater.start_polling()
        logger.info('Start polling...')
        updater.idle()


if __name__ == '__main__':
    main()
