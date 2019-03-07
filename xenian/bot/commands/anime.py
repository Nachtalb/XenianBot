from random import choice

from telegram import Animation, ParseMode
from telegram.ext import Filters, MessageHandler, run_async

from xenian.bot.commands import filters
from xenian.bot.models import Gif
from .base import BaseCommand

__all__ = ['anime']


class Anime(BaseCommand):
    """A set of base commands which every bot should have
    """

    group = 'Anime'

    def __init__(self):
        self.commands = [
            {'command': self.random, 'description': 'Send random anime GIF'},
            {
                'command': self.toggle_mode,
                'command_name': 'toggle_gif_save',
                'hidden': True,
                'options': {'filters': filters.bot_admin & ~ Filters.group},
            },
            {
                'command': self.save_gif_command,
                'command_name': 'save_gif',
                'hidden': True,
                'options': {'filters': filters.bot_admin},
            },
            {
                'title': 'Save Anime Gif',
                'handler': MessageHandler,
                'command': self.save_gif,
                'hidden': True,
                'options': {
                    'filters': (
                            Filters.animation
                            & filters.bot_admin
                            & filters.anime_save_mode
                            & ~ Filters.group
                    )
                },
            },
        ]

        super(Anime, self).__init__()

    def toggle_mode(self, *args, **kwargs):
        """Toggle gif save mode
        """
        self.tg_user.giv_save_mode = not self.tg_user.giv_save_mode
        self.tg_user.save()

        self.message.reply_text('GIF save mode turned `%s`' % ('on' if self.tg_user.giv_save_mode else 'off'),
                                parse_mode=ParseMode.MARKDOWN)

    def save_gif(self, *args, **kwargs):
        """Save a gif
        """
        attachment = self.message.effective_attachment or self.message.reply_to_message.effective_attachment

        if Gif.objects(file_id=attachment['file_id']).first():
            self.message.reply_text('GIF was already saved')
            return

        Gif(**attachment.to_dict()).save()
        self.message.reply_text(f'GIF was saved [{Gif.objects().count()}]')

    @run_async
    def random(self, *args, **kwargs):
        """Send one random anime GIF
        """
        gif = choice(Gif.objects().all())
        self.message.reply_animation(animation=gif.file_id)

    def save_gif_command(self, *args, **kwargs):
        """Save gif in reply
        """
        if not self.message.reply_to_message or not self.message.reply_to_message.animation:
            self.message.reply_text('You have to reply to a GIF')
            return
        self.save_gif()


anime = Anime()
