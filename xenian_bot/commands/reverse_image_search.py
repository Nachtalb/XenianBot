import io
import os
from tempfile import NamedTemporaryFile
from uuid import uuid4

from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Bot, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Filters, run_async
from telegram.ext.messagehandler import MessageHandler

from xenian_bot.commands.reverse_image_search_engines.bing import BingReverseImageSearchEngine
from xenian_bot.commands.reverse_image_search_engines.google import GoogleReverseImageSearchEngine
from xenian_bot.commands.reverse_image_search_engines.iqdb import IQDBReverseImageSearchEngine
from xenian_bot.commands.reverse_image_search_engines.tineye import TinEyeReverseImageSearchEngine
from xenian_bot.commands.reverse_image_search_engines.yandex import YandexReverseImageSearchEngine
from . import BaseCommand

__all__ = ['reverse_image_search_image', 'reverse_image_search_sticker', 'reverse_image_search_video']


class ReverseImageSearchMixin:

    def reverse_image_search(self, bot: Bot, update: Update, media_file: object, image_extension: str = None):
        """Send a reverse image search link for the image sent to us

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            media_file: File like image to search for
            image_extension (:obj:`str`): What extension the image should have. Default is 'jpg'
        """

        image_extension = image_extension or 'jpg'
        image_name = 'irs-' + str(uuid4())[:8]

        iqdb_search, google_search, tineye_search, bing_search, yandex_search = (
            IQDBReverseImageSearchEngine(), GoogleReverseImageSearchEngine(), TinEyeReverseImageSearchEngine(),
            BingReverseImageSearchEngine(), YandexReverseImageSearchEngine()
        )

        image_url = iqdb_search.upload_image(media_file, image_name + '.' + image_extension)

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
        update.message.reply_text(
            text=reply,
            reply_markup=reply_markup
        )


class ReverseImageSearchVideo(ReverseImageSearchMixin, BaseCommand):
    handler = MessageHandler

    def __init__(self):
        super(ReverseImageSearchVideo, self).__init__()
        self.options = {
            'filters': Filters.video | Filters.document,
            'callback': self.command
        }

    def command(self, bot: Bot, update: Update):
        """Send a reverse image search link for the GIF sent to us

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Please wait for your results ...')
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        document = update.message.document or update.message.video
        video = bot.getFile(document.file_id)

        with NamedTemporaryFile() as video_file:
            video.download(out=video_file)
            video_clip = VideoFileClip(video_file.name, audio=False)

            with NamedTemporaryFile(suffix='.gif') as gif_file:
                video_clip.write_gif(gif_file.name)

                dirname = os.path.dirname(gif_file.name)
                file_name = os.path.splitext(gif_file.name)[0]
                compressed_gif_path = os.path.join(dirname, file_name + '-min.gif')

                os.system('gifsicle -O3 --lossy=50 -o {dst} {src}'.format(dst=compressed_gif_path, src=gif_file.name))
                if os.path.isfile(compressed_gif_path):
                    self.reverse_image_search(bot, update, compressed_gif_path, 'gif')
                else:
                    self.reverse_image_search(bot, update, gif_file.name, 'gif')


reverse_image_search_video = ReverseImageSearchVideo()


class ReverseImageSearchSticker(ReverseImageSearchMixin, BaseCommand):
    handler = MessageHandler

    def __init__(self):
        super(ReverseImageSearchSticker, self).__init__()
        self.options = {
            'filters': Filters.sticker,
            'callback': self.command
        }

    @run_async
    def command(self, bot: Bot, update: Update):
        """Send a reverse image search link for the image of the sticker sent to us

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Please wait for your results ...')
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        sticker_image = bot.getFile(update.message.sticker.file_id)
        converted_image = io.BytesIO()

        with io.BytesIO() as image_buffer:
            sticker_image.download(out=image_buffer)
            with io.BufferedReader(image_buffer) as image_file:
                pil_image = Image.open(image_file).convert("RGBA")
                pil_image.save(converted_image, 'png')

                self.reverse_image_search(bot, update, converted_image, 'png')


reverse_image_search_sticker = ReverseImageSearchSticker()


class ReverseImageSearchImage(ReverseImageSearchMixin, BaseCommand):
    handler = MessageHandler

    def __init__(self):
        super(ReverseImageSearchImage, self).__init__()
        self.options = {
            'filters': Filters.photo,
            'callback': self.command
        }

    @run_async
    def command(self, bot: Bot, update: Update):
        """Send a reverse image search link for the image he sent us to the client

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        update.message.reply_text('Please wait for your results ...')
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        photo = bot.getFile(update.message.photo[-1].file_id)
        with io.BytesIO() as image_buffer:
            photo.download(out=image_buffer)
            with io.BufferedReader(image_buffer) as image_file:
                self.reverse_image_search(bot, update, image_file)


reverse_image_search_image = ReverseImageSearchImage()
