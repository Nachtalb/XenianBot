from telegram import Bot, Update
from telegram.ext import CommandHandler, MessageHandler, run_async
from telegram.parsemode import ParseMode
from yandex_translate import YandexTranslate

from xenian_bot.settings import SUPPORTER, ADMINS, YANDEX_API_TOKEN
from xenian_bot.utils import data, get_option_from_string
from .base import BaseCommand

__all__ = ['yandex']


class Yandex(BaseCommand):
    """A set of yandex api commands

    Attributes:
        translator (:obj:`YandexTranslate`): Translator object
    """

    translator = None

    def __init__(self):
        self.commands = [
            {
                'command': self.translate,
                'title': 'Translation by Yandex',
                'description': 'Translate a reply or a given text from `-lf` (default: detect) language to `-lt` '
                               '(default: en) language',
                'args': '[TEXT] [-lf LANG] [-lt LANG]'
            },
        ]

        self.translator = YandexTranslate(YANDEX_API_TOKEN)

        super(Yandex, self).__init__()

    @run_async
    def translate(self, bot: Bot, update: Update):
        """User can use /error to let all supporter / admin know about a bug or something else which has gone wrong

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        primary_text = None
        secondary_text = None

        reply_to_message = update.message.reply_to_message
        if reply_to_message:
            primary_text = reply_to_message.text

        split_text = update.message.text.split(' ', 1)
        if len(split_text) > 1:
            secondary_text = split_text[1]

        direction = 'en'
        if secondary_text:
            translate_from, new_text = get_option_from_string('lf', secondary_text)
            if translate_from:
                if translate_from not in self.translator.langs:
                    update.message.reply_text('Given language (`{}`) is not available'.format(translate_from))
                    return
                secondary_text = new_text

            translate_to, new_text = get_option_from_string('lt', secondary_text)
            if translate_to:
                if translate_to not in self.translator.langs:
                    update.message.reply_text('Given language (`{}`) is not available'.format(translate_to))
                    return
                secondary_text = new_text
            else:
                translate_to = 'en'

            direction = '{}-{}'.format(translate_from, translate_to) if translate_from else translate_to

            if not primary_text:
                primary_text = secondary_text

        if not primary_text and not secondary_text:
            update.message.reply_text('You either have to reply to a message or give me some text.')
            return

        translated = self.translator.translate(primary_text, direction)

        reply = '*TRANSLATION*: `{direction}`\n\n{translate_text}\n\n- Powered by Yandex.Translate'.format(
            direction=translated['lang'],
            translate_text=translated['text'][0]
        )
        update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


yandex = Yandex()
