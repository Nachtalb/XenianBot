from googletrans import Translator
from googletrans.constants import LANGUAGES
from googletrans.models import Translated
from telegram import Bot, Update
from telegram.ext import run_async
from telegram.parsemode import ParseMode

from xenian.bot.utils import get_option_from_string

from .base import BaseCommand

__all__ = ["translate"]


class Translate(BaseCommand):
    """A set of translate functions

    Attributes:
        translator (:obj:`googletrans.Translator`): Translator object
    """

    group = "Misc"

    def __init__(self):
        self.commands = [
            {
                "command": self.translate,
                "title": "Translate",
                "description": (
                    "Translate a reply or a given text from `-lf` (default: detect) language to `-lt` "
                    "(default: en) language"
                ),
                "args": ["text", "-lf LANG", "-lt LANG"],
            },
        ]

        self.translator = Translator()

        super(Translate, self).__init__()

    @run_async
    def translate(self, bot: Bot, update: Update):
        """Translate the given text

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not update.message:
            return
        primary_text = None
        secondary_text = None

        reply_to_message = update.message.reply_to_message
        if reply_to_message:
            primary_text = reply_to_message.text

        split_text = update.message.text.split(" ", 1)
        if len(split_text) > 1:
            secondary_text = split_text[1]

        translate_from = None
        translate_to = None
        if secondary_text:
            translate_from, new_text = get_option_from_string("lf", secondary_text)
            if translate_from:
                if translate_from not in LANGUAGES:
                    update.message.reply_text("Given language (`{}`) is not available".format(translate_from))
                    return
                secondary_text = new_text

            translate_to, new_text = get_option_from_string("lt", secondary_text)
            if translate_to:
                if translate_to not in LANGUAGES:
                    update.message.reply_text("Given language (`{}`) is not available".format(translate_to))
                    return
                secondary_text = new_text
            else:
                translate_to = "en"

            if not primary_text:
                primary_text = secondary_text

        if not primary_text and not secondary_text:
            update.message.reply_text("You either have to reply to a message or give me some text.")
            return

        translated = self.translator.translate(primary_text, translate_to or "en", translate_from or "auto")

        reply = "*TRANSLATION*: `{direction}`\n\n{translate_text}".format(
            direction=f"{translated.src} -> {translated.dest}",
            translate_text=translated.text,
        )
        update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


translate = Translate()
