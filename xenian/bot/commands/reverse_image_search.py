from uuid import uuid4
import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import Filters, run_async
from telegram.ext.messagehandler import MessageHandler

from xenian.bot.commands.filters import download_mode_filter
from xenian.bot.commands.reverse_image_search_engines.bing import BingReverseImageSearchEngine
from xenian.bot.commands.reverse_image_search_engines.google import GoogleReverseImageSearchEngine
from xenian.bot.commands.reverse_image_search_engines.iqdb import IQDBReverseImageSearchEngine
from xenian.bot.commands.reverse_image_search_engines.tineye import TinEyeReverseImageSearchEngine
from xenian.bot.commands.reverse_image_search_engines.yandex import YandexReverseImageSearchEngine
from xenian.bot.utils import auto_download
from . import BaseCommand

__all__ = ['reverse_image_search']


class ReverseImageSearch(BaseCommand):
    """Reverse Image Search integration for this bot
    """

    group = 'Image'

    def __init__(self):
        self.commands = [
            {
                'title': 'Auto Search',
                'description': 'Turn off /download_mode and send some kind of media file.',
                'command': self.auto_search,
                'handler': MessageHandler,
                'options': {
                    'filters': (
                            (Filters.video | Filters.document | Filters.photo | Filters.sticker)
                            & ~ Filters.group
                            & ~ Filters.reply
                            & ~ download_mode_filter
                    )
                }
            },
            {
                'title': 'Reply reverse search',
                'description': 'Reply to media for reverse search',
                'command': self.reply_search,
                'command_name': 'search'
            }
        ]

        super(ReverseImageSearch, self).__init__()

    @run_async
    def reply_search(self, bot: Bot, update: Update):
        """Reply to media to reverse search

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not update.message.reply_to_message:
            update.message.reply_text('You have to reply to some media file to start the reverse search.')
            return
        self.auto_search(bot, update)

    @run_async
    def auto_search(self, bot: Bot, update: Update):
        """Auto reverse search with the given message

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        message = update.message.reply_text('Please wait for the media file to be processed...')
        with auto_download(bot, update, convert_video_to_gif=True) as file_path:
            if file_path:
                self.reverse_image_search(bot, update, file_path, message)
            else:
                update.message.reply_text('Something went wrong contact and admin /error <TEXT> or try again later')

    def reverse_image_search(self, bot: Bot, update: Update, media_file: str, message: Message = None):
        """Send a reverse image search link for the image sent to us

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            media_file (:obj:`str`): Path to file to search for
            message (:obj:`telegram.message.Message`, optional): An message object to update. Instead of sending a new
        """

        image_extension = os.path.splitext(media_file)[1]
        image_name = 'irs-' + str(uuid4())[:8]

        iqdb_search, google_search, tineye_search, bing_search, yandex_search = (
            IQDBReverseImageSearchEngine(), GoogleReverseImageSearchEngine(), TinEyeReverseImageSearchEngine(),
            BingReverseImageSearchEngine(), YandexReverseImageSearchEngine()
        )

        image_url = iqdb_search.upload_image(media_file, image_name + image_extension, remove_after=3600)

        if os.path.isfile(image_url):
            reply = 'This bot is not configured for this functionality, contact an admin for more information /support.'
            if message:
                message.edit_text(reply, reply_to_message_id=update.message.message_id)
            else:
                update.message.reply_text(reply, reply_to_message_id=update.message.message_id)
            return

        iqdb_url, google_url, tineye_url, bing_url, yandex_url = (
            iqdb_search.get_search_link_by_url(image_url), google_search.get_search_link_by_url(image_url),
            tineye_search.get_search_link_by_url(image_url), bing_search.get_search_link_by_url(image_url),
            yandex_search.get_search_link_by_url(image_url)
        )

        button_list = [[
            InlineKeyboardButton(text='Go To Image', url=image_url)
        ], [
            InlineKeyboardButton(text='IQDB', url=iqdb_url),
            InlineKeyboardButton(text='GOOGLE', url=google_url),
        ], [
            InlineKeyboardButton(text='YANDEX', url=yandex_url),
            InlineKeyboardButton(text='BING', url=bing_url),
        ], [
            InlineKeyboardButton(text='TINEYE', url=tineye_url),
        ]]

        reply = 'Tap on the search engine of your choice.'
        reply_markup = InlineKeyboardMarkup(button_list)
        if message:
            bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=message.message_id,
                text=reply,
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text=reply,
                reply_markup=reply_markup
            )


reverse_image_search = ReverseImageSearch()
