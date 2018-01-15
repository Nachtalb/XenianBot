from tempfile import NamedTemporaryFile

from telegram import Bot, Update
from telegram.ext import Filters, MessageHandler

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
