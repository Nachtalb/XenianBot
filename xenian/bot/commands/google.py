import os
from uuid import uuid4

from gtts import gTTS
from telegram import Bot, Update, ChatAction
from telegram.ext import run_async

from xenian.bot.utils import CustomNamedTemporaryFile
from xenian.bot.utils import get_option_from_string
from .base import BaseCommand

__all__ = ['google']


class Google(BaseCommand):
    """A set of commands using google API's
    """

    group = 'Misc'

    def __init__(self):
        self.commands = [
            {
                'command_name': 'tty',
                'command': self.text_to_speech,
                'description': 'Convert text the given text or the message replied to, to text. Use `-l` to define a '
                               'language, like de, en or ru',
                'args': ['text', '-l LANG']
            },
        ]

        super(Google, self).__init__()

    @run_async
    def text_to_speech(self, bot: Bot, update: Update):
        """Convert the given text to speech and send it as mp3

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        primary_text = update.message.reply_to_message.text if update.message.reply_to_message else ''
        secondary_text = ''
        split_text = update.message.text.split(' ', 1)
        if len(split_text) > 1:
            secondary_text = split_text[1]

        speak_in, new_text = get_option_from_string('l', secondary_text)
        if speak_in:
            if speak_in not in gTTS.LANGUAGES:
                update.message.reply_text('Given language (`{}`) is not available'.format(speak_in))
                return
            secondary_text = new_text
        else:
            speak_in = 'en'

        if not primary_text:
            primary_text = secondary_text

        if not primary_text and not secondary_text:
            update.message.reply_text('You either have to reply to a message or give me some text.')
            return

        with CustomNamedTemporaryFile() as mp3_file:
            bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.RECORD_AUDIO)
            try:
                spoken = gTTS(primary_text, lang=speak_in)
                spoken.save(mp3_file.name)
            except ValueError:
                update.message.reply_text('Could not translate {}'.format(primary_text))
                return
            except BaseException as error:
                update.message.reply_text('An error occurred, please try again later or contact the bot owner /error.')
                raise error

            filename = 'XenianBot-TTS-{lang}-{text}-{random}.mp3'.format(
                lang=speak_in,
                text=primary_text[:10].strip(),
                random=str(uuid4())[:8]
            )
            os.link(mp3_file.name, os.path.join(os.path.dirname(mp3_file.name), filename))

            update.message.reply_audio(
                audio=mp3_file,
                performer='Google',
                title=os.path.splitext(filename)[0],
                caption=primary_text,
            )


google = Google()
