import os
from tempfile import NamedTemporaryFile
from uuid import uuid4

from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Bot, ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Filters, MessageHandler

from xenian_bot.settings import UPLOADER
from xenian_bot.uploaders import uploader
from xenian_bot.utils import build_menu
from . import BaseCommand
from .filters.download_mode import download_mode_filter

__all__ = ['toggle_download_mode', 'convert_stickers']


class ToggleDownloadMode(BaseCommand):
    command_name = 'download_mode'
    title = 'Toggle Download Mode on / off'
    description = 'Download stickers and gifs in download mode'

    def command(self, bot: Bot, update: Update):
        """Toggle Download Mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        mode_on = download_mode_filter.toggle_mode(update.message.from_user.username)
        if mode_on:
            update.message.reply_text('Download Mode on')
        else:
            update.message.reply_text('Download Mode off')


toggle_download_mode = ToggleDownloadMode()


class ConvertSticker(BaseCommand):
    handler = MessageHandler
    title = 'Download Stickers'
    description = 'Turn /download_mode on and send stickers'

    def __init__(self):
        super(ConvertSticker, self).__init__()
        self.options = {
            'callback': self.command,
            'filters': Filters.sticker & download_mode_filter
        }

    def command(self, bot: Bot, update: Update):
        """Download Sticker as images

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        sticker = bot.get_file(update.message.sticker.file_id)
        with NamedTemporaryFile() as image:
            sticker.download(image.name)
            bot.send_photo(update.message.chat_id, photo=image)


convert_stickers = ConvertSticker()


class DownloadGif(BaseCommand):
    handler = MessageHandler
    title = 'Download Gifs'
    description = 'Turn /download_mode on and send videos'

    def __init__(self):
        super(DownloadGif, self).__init__()
        self.options = {
            'callback': self.command,
            'filters': (Filters.video | Filters.document) & download_mode_filter
        }

    def command(self, bot: Bot, update: Update):
        """Download videos as gifs

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        document = (update.message.document or update.message.video or update.message.reply_to_message.document or
                    update.message.reply_to_message.video)
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
                    path = compressed_gif_path
                else:
                    path = gif_file.name

                upload_file_name = 'xenian-{}.gif'.format(str(uuid4())[:8])

                uploader.connect()
                uploader.upload(path, upload_file_name)
                uploader.close()

                path = UPLOADER.get('url', None) or UPLOADER['configuration'].get('path', None) or ''
                host_path = path + '/' + upload_file_name

                button_list = [
                    InlineKeyboardButton("Open", url=host_path),
                ]
                reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
                bot.send_message(update.message.chat_id, 'Instant GIF Download',  reply_markup=reply_markup)


download_gif = DownloadGif()
