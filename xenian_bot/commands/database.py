from pymongo import MongoClient
from telegram import Bot, Chat, Message, Update, User
from telegram.ext import MessageHandler, run_async, Handler, Filters

from xenian_bot import mongodb_database
from .base import BaseCommand

__all__ = ['database']


class Database(BaseCommand):
    """A set of database commands

    Attributes:
        users (:obj:`pymongo.collection.Collection`): Connection to the pymongo databased
    """

    name = 'Bot Helpers'

    def __init__(self):
        self.commands = [
            {
                'command': self.add_to_database_command,
                'title': 'Add to Database',
                'description': 'Adds user, message and chat to database',
                'handler': MessageHandler,
                'group': 1
            },
        ]

        self.users = mongodb_database.users
        self.chats = mongodb_database.chats
        self.messages = mongodb_database.messages

        super(Database, self).__init__()

    @run_async
    def add_to_database_command(self, bot: Bot, update: Update):
        """Add a user to the database if he is not already in it

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        self.upsert_chat(update.effective_chat)
        self.upsert_message(update.effective_message)
        self.upsert_user(update.effective_user)

    def upsert_user(self, user: User):
        """Insert or if existing update user

        Args:
            user (:obj:`telegram.user.User`): Telegram Api User Object
        """
        self.users.update({'id': user.id}, user.to_dict(), upsert=True)

    def upsert_message(self, message: Message):
        """Insert or if existing update message

        Args:
            message (:obj:`telegram.message.Message`): Telegram Api Message Object
        """
        self.messages.update({'message_id': message.message_id}, message.to_dict(), upsert=True)

    def upsert_chat(self, chat: Chat):
        """Insert or if existing update chat

        Args:
            chat (:obj:`telegram.chat.Chat`): Telegram Api Chat Object
        """
        self.chats.update({'id': chat.id}, chat.to_dict(), upsert=True)


database = Database()
