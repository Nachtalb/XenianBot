from telegram import Audio, Bot, Document, ParseMode, PhotoSize, Sticker, Update, Video
from telegram.ext import Filters, MessageHandler

from xenian_bot import mongodb_database
from xenian_bot.commands import filters
from .base import BaseCommand

__all__ = ['image_db']


class CustomDB(BaseCommand):
    """Create Custom Databases by chat_id and tag
    """

    group = 'Custom'

    def __init__(self):
        self.commands = [
            {
                'command': self.toggle_mode,
                'description': 'Create an custom database',
                'args': ['tag'],
                'command_name': 'save_mode',
                'options': {
                    'filters': ~ Filters.group,
                    'pass_args': True,
                },
            },
            {
                'title': 'Save object',
                'command': self.save_command,
                'command_name': 'save',
                'description': 'Reply to save an object to a custom db',
                'args': ['tag'],
                'options': {
                    'pass_args': True,
                },
            },
            {
                'title': 'Save object',
                'description': 'Send objects while /save_mode is turned of to save them into your defined db',
                'handler': MessageHandler,
                'command': self.save,
                'options': {
                    'filters': (
                            (
                                    Filters.video
                                    | Filters.document
                                    | Filters.photo
                                    | Filters.sticker
                                    | Filters.audio
                                    | Filters.voice
                                    | Filters.text
                            )
                            & filters.custom_db_save_mode
                            & ~ Filters.group
                    ),
                },
            },
        ]
        self.telegram_object_collection = mongodb_database.telegram_object_collection
        self.custom_db_save_mode = mongodb_database.custom_db_save_mode

        super(CustomDB, self).__init__()

    def get_current_tag(self, update: Update, tags: list = None):
        """Get the current active tag

        Args:
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            tags (:obj:`list`, optional): List of tags sent by the user if it is is set the first one will be taken

        Returns:
            :obj:`str`: The currently active tag for this user
        """
        if tags:
            return tags[0].lower()

        chat = self.custom_db_save_mode.find_one({'chat_id': update.message.chat_id})
        if chat and chat.get('tag', ''):
            return chat['tag'].lower()
        return ''

    def toggle_mode(self, bot: Bot, update: Update, args: list = None):
        """Toggle save mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        tag = 'user'
        if args:
            tag = args[0].lower()

        chat_id = update.message.chat_id
        data = self.custom_db_save_mode.find_one({'chat_id': chat_id})
        new_mode = not data['mode'] if data else True
        self.custom_db_save_mode.update({'chat_id': chat_id},
                                        {'chat_id': chat_id, 'mode': new_mode, 'tag': tag},
                                        upsert=True)
        if new_mode:
            update.message.reply_text('Save mode turned of for `[%s]`. You can send me any type of Telegram object not '
                                      'to save it.' % tag, parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text('Save mode turned off')

    def save_command(self, bot: Bot, update: Update, args: list = None):
        """Save image in reply

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        reply_to_message = update.message.reply_to_message
        if not reply_to_message:
            update.message.reply_text('You have to reply to some media file.')
            return
        tag = self.get_current_tag(update, args)
        self.save(bot, update, tag)

    def save(self, bot: Bot, update: Update, tag: str = None):
        """Save a gif

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            tag (:obj:`tag`, optional): Tag for the image
        """

        reply_to = False
        telegram_object = (
                update.message.document
                or update.message.video
                or update.message.photo
                or update.message.sticker
                or update.message.audio
                or update.message.voice
        )
        if not telegram_object:
            if getattr(update.message, 'reply_to_message'):
                telegram_object = (
                        update.message.reply_to_message.document
                        or update.message.reply_to_message.video
                        or update.message.reply_to_message.photo
                        or update.message.reply_to_message.sticker
                        or update.message.reply_to_message.audio
                        or update.message.reply_to_message.voice
                        or update.message.reply_to_message.text
                )
            reply_to = bool(telegram_object)
            if not reply_to:
                telegram_object = update.message.text

        if not telegram_object:
            update.message.reply_text('You either have to send something or reply to something')
            return

        message = None
        if not tag:
            tag = self.get_current_tag(update)

        if isinstance(telegram_object, str):
            message = {
                'type': 'text',
                'text': telegram_object,
                'file_id': '',
            }
        else:
            message = {
                'type': 'document',
                'text': (getattr(update.message.reply_to_message, 'caption') if reply_to
                         else getattr(update.message, 'caption')),
                'file_id': telegram_object.file_id,
            }
            if isinstance(telegram_object, Document):
                message['type'] = 'document'
            elif isinstance(telegram_object, Video):
                message['type'] = 'video'
            elif isinstance(telegram_object, PhotoSize):
                message['type'] = 'photo'
            elif isinstance(telegram_object, Sticker):
                message['type'] = 'sticker'
            elif isinstance(telegram_object, Audio):
                message['type'] = 'audio'

        if not message:
            update.message.reply_text('There was an error please contact an admin via /error or retry your action.')
            return

        message['chat_id'] = update.message.chat_id
        message['tag'] = tag
        self.telegram_object_collection.update(message, message, upsert=True)

        update.message.reply_text('{} was saved!'.format(message['type'].title()), parse_mode=ParseMode.MARKDOWN)


image_db = CustomDB()
