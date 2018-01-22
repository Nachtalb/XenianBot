import logging
import os
import sys
from threading import Thread

from telegram import Bot, TelegramError, Update
from telegram.ext import CommandHandler, Filters, Updater

import xenian_bot
from .commands import BaseCommand
from .settings import ADMINS, MODE, TELEGRAM_API_TOKEN

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
        bot.send_message(chat_id=update.effective_chat.id, text='Whoops, there was an error. Please try again.')


def main():
    global job_queue
    updater = Updater(TELEGRAM_API_TOKEN)
    dispatcher = updater.dispatcher

    xenian_bot.job_queue = updater.job_queue

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

    for command_class in BaseCommand.all_commands:
        for command in command_class.commands:
            dispatcher.add_handler(command['handler'](**command['options']))

    # log all errors
    dispatcher.add_error_handler(error)

    if MODE['active'] == 'webhook':
        webhook = MODE['webhook']
        updater.start_webhook(listen=webhook['listen'], port=webhook['port'], url_path=webhook['url_path'])
        updater.bot.set_webhook(url=webhook['url'])
        logger.info('Starting webhook...')
    else:
        updater.start_polling()
        logger.info('Start polling...')
        updater.idle()


if __name__ == '__main__':
    main()
