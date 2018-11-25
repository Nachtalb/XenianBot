from telegram import Audio, Bot, Chat, Document, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, PhotoSize, \
    Sticker, Update, Video
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler, run_async

from xenian.bot import mongodb_database
from xenian.bot.commands import filters
from xenian.bot.utils import render_template, user_is_admin_of_group
from .base import BaseCommand

__all__ = ['image_db']


class CustomDB(BaseCommand):
    """Create Custom Databases by chat_id and tag
    """

    group = 'Custom'
    ram_db = {}

    def __init__(self):
        self.commands = [
            {
                'command': self.pre_toggle_mode,
                'description': 'Start database save mode and send your objects',
                'command_name': 'save_mode',
                'args': ['tag'],
                'options': {
                    'filters': ~ Filters.group,
                    'pass_args': True
                },
            },
            {
                'command': self.toggle_mode,
                'handler': CallbackQueryHandler,
                'options': {
                    'pattern': '^toggle_save_mode\s\w+$',
                },
            },
            {
                'title': 'Save object',
                'command': self.save_command,
                'command_name': 'save',
                'description': 'Reply to save an object to a custom database',
                'args': ['tag'],
                'options': {
                    'pass_args': True,
                },
            },
            {
                'title': 'Save object',
                'command': self.save_command,
                'handler': CallbackQueryHandler,
                'hidden': True,
                'options': {
                    'pattern': '^save\s\w+$',
                },
            },
            {
                'title': 'Available DBs',
                'command': self.command_wrapper(self.show_tag_chooser, 'info', 'Select a database to see it\'s info:'),
                'command_name': 'db_info',
                'description': 'Show created databases',
            },
            {
                'title': 'Available DBs',
                'command': self.show_info,
                'handler': CallbackQueryHandler,
                'description': 'Show info about created databases',
                'options': {
                    'pattern': '^(info\s\w+)$',
                },
            },
            {
                'title': 'Remove DB',
                'command': self.command_wrapper(self.show_tag_chooser, 'sure', 'Select the database to delete:'),
                'command_name': 'delete_db',
                'description': 'Delete selected database',
                'options': {
                    'filters': filters.user_group_admin_if_group,
                }
            },
            {
                'title': 'Remove DB',
                'command': self.real_delete,
                'handler': CallbackQueryHandler,
                'description': 'Delete the database for real',
                'options': {
                    'pattern': '^(delete\s\w+|sure\s\w+|cancel)$',
                }
            },
            {
                'title': 'Show available tags as keyboard buttons',
                'command': self.show_tag_chooser,
                'handler': CallbackQueryHandler,
                'hidden': True,
                'options': {
                    'pattern': '^show_tags',
                }
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

    def is_group_admin_if_group(self, update: Update):
        """Check if current user is admin of current group if the chat is one

        Args:
            update (:obj:`telegram.update.Update`): Telegram Api Update Object

        Returns:
            :obj:`bool`: True if he is admin or this chat is not a group
         """
        return not (update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]
                    and not user_is_admin_of_group(update.effective_chat, update.effective_user))

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

    def pre_toggle_mode(self, bot: Bot, update: Update, args: list = None):
        """Pre Toggle save mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        tag = args[0] if args else None
        data = self.custom_db_save_mode.find_one({'chat_id': update.effective_chat.id})
        current_mode = data['mode'] if data else False

        if current_mode:
            self.toggle_mode(bot, update)
        else:
            if tag:
                self.toggle_mode(bot, update, tag)
            else:
                self.show_tag_chooser(bot, update, 'toggle_save_mode', 'Choose a database:')

    def toggle_mode(self, bot: Bot, update: Update, tag: str = None):
        """Toggle save mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            tag (:obj:`str`): Name for the tag
        """
        tag = tag or ''
        if getattr(update, 'callback_query', None):
            tag = update.callback_query.data.split(' ')[1]

        chat_id = update.effective_chat.id
        data = self.custom_db_save_mode.find_one({'chat_id': chat_id})
        new_mode = not data['mode'] if data else True
        self.custom_db_save_mode.update({'chat_id': chat_id},
                                        {'chat_id': chat_id, 'mode': new_mode, 'tag': tag},
                                        upsert=True)
        if new_mode:
            text = 'Save mode turned on for `[%s]`. You can send me any type of Telegram object to save it.' % tag
            if getattr(update, 'callback_query', None):
                update.callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            bot.send_message(chat_id, 'Save mode turned off')

    @run_async
    def show_tag_chooser(self, bot: Bot, update: Update, method: str = None, message: str = None):
        """Show available tags in inline-keyboard-buttons

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            method (:obj:`str`, optional): Method to call when clicked (callback query method), is obligatory if you
                method is not called by the bot itself
            message (:obj:`str`, optional): Message to send to the user
        """
        callback_query, message = self.callbackquery_handler(update, method, message)
        if callback_query is None:
            return

        message = message or 'Choose a tag:'

        db_items = self.telegram_object_collection.find({'chat_id': update.message.chat_id})
        tag_list = list(set([item['tag'] for item in db_items]))
        if tag_list:
            button_list = [tag_list[i:i + 3] for i in range(0, len(tag_list), 3)]
            button_list = [
                [InlineKeyboardButton(tag, callback_data='{} {}'.format(method, tag)) for tag in group]
                for group in button_list
            ]
        else:
            button_list = [[InlineKeyboardButton('user', callback_data='%s user' % method)]]

        button_list.append([InlineKeyboardButton('Cancel', callback_data='show_tags cancel')])

        buttons = InlineKeyboardMarkup(button_list)
        if callback_query:
            callback_query.message.edit(message, reply_markup=buttons)
        else:
            update.message.reply_text(message, reply_markup=buttons)

    def save_command(self, bot: Bot, update: Update, args: list = None):
        """Save image in reply

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        if (update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]
                and not user_is_admin_of_group(update.effective_chat, update.effective_user)):
            if update.message:
                update.message.reply_text('Only admins can use this command in groups')
            return

        self.ram_db.setdefault('save_reply', {})
        reply_to_message = getattr(update.message, 'reply_to_message', None)
        previous_message = self.ram_db['save_reply'].get(update.effective_user.id, None)
        if not reply_to_message and not previous_message:
            update.message.reply_text('You have to reply to some message.')
            return

        callback_query = getattr(update, 'callback_query', None)
        if callback_query:
            args = list(set(callback_query.data.split(' ')) - {'save'})
            callback_query.message.delete()
            update.message = previous_message
        elif not args:
            self.ram_db['save_reply'][update.effective_user.id] = update.message
            self.show_tag_chooser(bot, update, 'save')
            return

        tag = self.get_current_tag(update, args)
        self.save(bot, update, tag)
        self.ram_db['save_reply'][update.effective_user.id] = None

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

        if isinstance(telegram_object, list):
            actual_object = None
            for object in telegram_object:
                if isinstance(object, PhotoSize) and (not actual_object or object.file_size > actual_object.file_size):
                    actual_object = object
            telegram_object = actual_object
            if not telegram_object:
                update.message.reply_text('An error occurred, please contact an admin with /error.')
                return

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

        update.message.reply_text('{} was saved to `{}`!'.format(message['type'].title(), tag),
                                  parse_mode=ParseMode.MARKDOWN)

    @run_async
    def show_info(self, bot: Bot, update: Update):
        """Show info about custom db

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """

        tag = update.callback_query.data.split(' ')[1]
        db_items = self.telegram_object_collection.find({'chat_id': update.effective_chat.id, 'tag': tag})
        data = {
            'tag': tag,
            'video': 0,
            'document': 0,
            'photo': 0,
            'sticker': 0,
            'audio': 0,
            'voice': 0,
            'text': 0,
            'total': 0
        }
        for item in db_items:
            data[item['type']] += 1
            data['total'] += 1

        update.callback_query.message.edit_text(text=render_template('db_info.html.mako', info=data),
                                                parse_mode=ParseMode.HTML)

    def real_delete(self, bot: Bot, update: Update):
        """Actually delete a databases

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if not self.is_group_admin_if_group(update):
            return

        data = update.callback_query.data
        if data.startswith('sure'):
            update.callback_query.message.edit_text(
                'Are you sure:',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('Yes', callback_data='delete %s' % data.split(' ')[1]),
                    InlineKeyboardButton('Cancel', callback_data='cancel'),
                ]])
            )
        elif data == 'cancel':
            update.callback_query.message.delete()
        elif data.startswith('delete'):
            tag = data.split(' ')[1]
            self.telegram_object_collection.delete_many({'chat_id': update.callback_query.message.chat_id, 'tag': tag})
            update.callback_query.message.edit_text('%s deleted!' % tag.title())
        else:
            update.callback_query.message.edit_text('Something went wrong, try again or contact admin via /error.')

    def callbackquery_handler(self, update, method, message):
        """Handle callbackqueries to a point where we can actually use them

        Args:
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            method (:obj:`str`, optional): Method to call when clicked (callback query method), is obligatory if you
                method is not called by the bot itself
            message (:obj:`str`, optional): Message to send to the user
        Returns:
            :obj:`tuple`: The first item will either be :obj:`False` if the request was not a callbackquery but still is
                valid or a :obj:`telegram.callbackquery.CallbackQuery` if the request was a callbackquery.
                The second item is either a :obj:`str`.
                Both values are :obj:`None` if something went wrong or the whole operation should be cancelled.
        Raises:
            :obj:`ValueError`: If no ``method`` and no ``callbackquery`` was set.
        """
        callback_query = getattr(update, 'callback_query', False) or False
        message = ''
        if not callback_query and not method:
            raise ValueError('Wither callback_query or method must be set')

        if callback_query:
            if not self.is_group_admin_if_group(update):
                return None, None
            args = callback_query.data.split(' ')
            args = list(filter(lambda string: string.strip() if string.strip() else None, args))

            if args[1] == 'cancel':
                update.callback_query.message.delete()
                return None, None

            if callback_query:
                method = args[1] if len(args) > 1 else ''
                if not method:
                    update.message.reply_text('Something went wrong, try again or contact an admin /error')
                    return None, None
            if len(args) > 2:
                message = ' '.join(args[2:])
        return callback_query, message


image_db = CustomDB()
