import logging
import os
import sys
from threading import Thread
from queue import Queue

from telegram import Bot, TelegramError, Update
from telegram.ext import CommandHandler, Filters, Updater, Dispatcher, JobQueue
from telegram.ext.messagequeue import queuedmessage, MessageQueue
from telegram.utils.request import Request

import xenian.bot
from xenian.bot.utils import get_self
from .commands import BaseCommand
from .settings import ADMINS, LOG_LEVEL, MODE, TELEGRAM_API_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOG_LEVEL)
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


class MQBot(Bot):
    def __init__(self, *args, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        self._is_messages_queued_default = True
        self._msg_queue  = MessageQueue(all_burst_limit=2,
                                        all_time_limit_ms=1024,
                                        group_burst_limit=19,
                                        group_time_limit_ms=6000)
    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass

    @queuedmessage
    def _message(self, *args, **kwargs):
        return super(MQBot, self,)._message(*args, **kwargs)

def main():
    workers = 8
    con_pool_size = workers + 4

    job_queue = JobQueue()

    request = Request(con_pool_size=con_pool_size)
    bot = MQBot(token=TELEGRAM_API_TOKEN, request=request)
    dispatcher = Dispatcher(bot, Queue(),
                           job_queue=job_queue,
                           workers=workers)
    job_queue.set_dispatcher(dispatcher)
    updater = Updater(dispatcher=dispatcher, workers=None)

    xenian.bot.job_queue = job_queue

    def on_start():
        self = get_self(updater.bot)
        logger.info(f'Acting as {self.name} [link: {self.link}, id: {self.id}], with the key "{TELEGRAM_API_TOKEN}"')

    def stop_and_restart(chat_id):
        """Gracefully stop the Updater and replace the current process with a new one.
        """
        logger.info('Restarting: stopping')
        updater.stop()
        logger.info('Restarting: starting')
        os.execl(sys.executable, sys.executable, *sys.argv + [f'is_restart={chat_id}'])

    def restart(bot: Bot, update: Update):
        """Start the restarting process

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Bot is restarting...')
        Thread(target=lambda: stop_and_restart(update.message.chat_id)).start()

    def send_message_if_reboot():
        args = sys.argv
        is_restart_arg = [item for item in args if item.startswith('is_restart')]
        if any(is_restart_arg):
            chat_id = is_restart_arg[0].split('=')[1]
            updater.bot.send_message(chat_id, 'Bot has successfully restarted.')

    dispatcher.add_handler(CommandHandler('restart', restart, filters=Filters.user(username=ADMINS)))

    for command_class in BaseCommand.all_commands:
        for command in command_class.commands:
            dispatcher.add_handler(command['handler'](**command['options']), command['group'])

    # log all errors
    dispatcher.add_error_handler(error)

    if MODE['active'] == 'webhook':
        webhook = MODE['webhook']
        updater.start_webhook(listen=webhook['listen'], port=webhook['port'], url_path=webhook['url_path'])
        updater.bot.set_webhook(url=webhook['url'])
        send_message_if_reboot()
        logger.info('Starting webhook...')
        on_start()
    else:
        updater.start_polling()
        logger.info('Start polling...')
        send_message_if_reboot()
        on_start()
        updater.idle()


if __name__ == '__main__':
    main()
