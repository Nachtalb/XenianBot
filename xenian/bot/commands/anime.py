from random import choice

from telegram import Bot, ParseMode, Update
from telegram.ext import Filters, MessageHandler, run_async

from xenian.bot import mongodb_database
from xenian.bot.commands import filters

from .base import BaseCommand

__all__ = ["anime"]


class Anime(BaseCommand):
    """A set of base commands which every bot should have"""

    group = "Anime"

    def __init__(self):
        self.commands = [
            {"command": self.random, "description": "Send random anime GIF"},
            {
                "command": self.toggle_mode,
                "command_name": "toggle_gif_save",
                "hidden": True,
                "options": {"filters": filters.bot_admin & ~Filters.group},
            },
            {
                "command": self.save_gif_command,
                "command_name": "save_gif",
                "hidden": True,
                "options": {"filters": filters.bot_admin},
            },
            {
                "title": "Save Anime Gif",
                "handler": MessageHandler,
                "command": self.save_gif,
                "hidden": True,
                "options": {
                    "filters": (
                        (Filters.video | Filters.document)
                        & filters.bot_admin
                        & filters.anime_save_mode
                        & ~Filters.group
                    )
                },
            },
        ]
        self.gif = mongodb_database.gifs
        self.gif_save_mode = mongodb_database.gif_save_mode

        super(Anime, self).__init__()

    def toggle_mode(self, bot: Bot, update: Update):
        """Toggle gif save mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not update.message:
            return
        chat_id = update.message.chat_id
        data = self.gif_save_mode.find_one({"chat_id": chat_id})
        new_mode = not data["mode"] if data else True
        self.gif_save_mode.update({"chat_id": chat_id}, {"chat_id": chat_id, "mode": new_mode}, upsert=True)
        update.message.reply_text(
            "GIF save mode turned `%s`" % ("on" if new_mode else "off"), parse_mode=ParseMode.MARKDOWN
        )

    def save_gif(self, bot: Bot, update: Update):
        """Save a gif

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        video = (
            update.message.document
            or update.message.video
            or update.message.reply_to_message.document
            or update.message.reply_to_message.video
        )

        if video.mime_type != "video/mp4":
            update.message.reply_text("This file is not supported, send GIFs or MP4 videos.")
            return
        self.gif.update({"file_id": video.file_id}, video.to_dict(), upsert=True)
        update.message.reply_text("GIF was saved")

    @run_async
    def random(self, bot: Bot, update: Update):
        """Send one random anime GIF

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        videos = list(self.gif.find())
        video = choice(videos)

        if video.get("duration", None):
            bot.send_video(update.message.chat_id, video["file_id"])
        else:
            bot.send_document(update.message.chat_id, video["file_id"])

    def save_gif_command(self, bot: Bot, update: Update):
        """Save gif in reply

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        reply_to_message = update.message.reply_to_message
        if not reply_to_message:
            update.message.reply_text("You have to reply to some media file.")
        if reply_to_message.video or reply_to_message.document:
            self.save_gif(bot, update)


anime = Anime()
