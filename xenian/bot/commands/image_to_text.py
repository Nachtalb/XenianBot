import io

import pytesseract
from PIL import Image
from pytesseract import TesseractError
from telegram import Bot, File, ParseMode, Update
from telegram.ext import run_async

from xenian.bot.settings import IMAGE_TO_TEXT_LANG
from xenian.bot.utils import get_option_from_string
from . import translate
from .base import BaseCommand

__all__ = ['image_to_text']


class ImageToText(BaseCommand):
    """Extract text from images
    """

    group = 'Image'

    def __init__(self):
        self.commands = [
            {
                'command': self.image_to_text,
                'command_name': 'itt',
                'title': 'Image to Text',
                'description': 'Extract text from images',
                'args': ['-l LANG']
            },
            {
                'command': self.image_to_text_translate,
                'command_name': 'itt_translate',
                'title': 'Image to Text Translation',
                'description': 'Extract text from images and translate it. `-lf` (default: detect, /itt_lang) language '
                               'on image, to `-lt` (default: en, normal language codes) language.',
                'args': ['text', '-lf LANG', '-lt LANG']
            },
            {
                'command': self.available_languages,
                'command_name': 'itt_lang',
                'title': 'Languages for ItT',
                'description': 'Available languages for Image to Text',
            },
        ]

        super(ImageToText, self).__init__()

    @run_async
    def available_languages(self, bot: Bot, update: Update):
        """Print available languages for image to text

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        text = '*Available languages for Image to Text(/itt)*:\n\n'
        for short, name in IMAGE_TO_TEXT_LANG:
            text += '`{}` -> {}\n'.format(short, name)

        self.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    @run_async
    def image_to_text(self, bot: Bot, update: Update):
        """Extract text from images

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.message.reply_to_message or not self.message.reply_to_message.photo:
            self.message.reply_text('You have to reply to an image.')
            return

        lang, text = get_option_from_string('l', self.message.text)

        photo = self.bot.getFile(self.message.reply_to_message.photo[-1].file_id)
        found_text = self.get_text_from_photo(photo, lang)

        if found_text:
            reply = f'*This text was found:*\n\n{found_text}'
        else:
            reply = 'No text was found. Make sure that the text is not rotated and good readable.'

        self.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    @run_async
    def image_to_text_translate(self, bot: Bot, update: Update):
        """Extract text from images and translate it

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.message.reply_to_message or not self.message.reply_to_message.photo:
            self.message.reply_text('You have to reply to an image.')
            return

        lang_from, text = get_option_from_string('lf', self.message.text)
        lang_to, text = get_option_from_string('lt', self.message.text)

        photo = self.bot.getFile(self.message.reply_to_message.photo[-1].file_id)
        found_text = self.get_text_from_photo(photo, lang_from)

        if found_text:
            translated = translate.translate_text(found_text, lang_to=lang_to)
            reply = (f'*Found Text:*\n{found_text}\n\n'
                     f'*Translation:* `{translated.src} -> {translated.dest}` \n\n'
                     f'{translated.text}')
        else:
            reply = 'No text was found. Make sure that the text is not rotated and good readable.'

        self.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

    def get_text_from_photo(self, photo: File, language: str) -> str:
        with io.BytesIO() as image_buffer:
            photo.download(out=image_buffer)

            pil_image = Image.open(image_buffer)
            try:
                return self.extract_text(pil_image, language)
            except TesseractError:
                return ''

    def extract_text(self, image: object or Image, lang: str = None) -> str:
        """Extract text from an image

        Works with tesseract

        Args:
            image (:obj:`Object` or :obj:`PIL.Image`): File like object or PIL Image
            lang (:obj:`str`): What is the language on the image

        Returns:
            :obj:`str`: Text found in image
        """
        return pytesseract.image_to_string(image, lang=lang)


image_to_text = ImageToText()
