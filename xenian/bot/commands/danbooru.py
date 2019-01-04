import re
from collections import OrderedDict

from pybooru import Danbooru as PyDanbooru
from telegram import Bot, ChatAction, InputMediaPhoto, Update
from telegram.error import BadRequest, TimedOut
from telegram.ext import run_async

from xenian.bot.settings import DANBOORU_API_TOKEN
from . import BaseCommand

__all__ = ['danbooru']


class Danbooru(BaseCommand):
    """The class for all danbooru related commands
    """
    group = 'Anime'

    def __init__(self):
        self.commands = [
            {
                'title': 'Danobooru Search',
                'description': 'Search on danbooru by max 2 tags separated by comma. You can define which page '
                               '(default 0) and the limit (default 5, max 100)',
                'command': self.danbooru_search,
                'options': {'pass_args': True},
                'args': ['tag_1', 'tag_2', 'page=PAGE_NUM', 'limit=LIMIT']
            },
            {
                'title': 'Danbooru Latest',
                'description': 'Get latest uploads from danbooru you can use the options page (default 0) and limit '
                               '(default 5, max 100)',
                'command': self.danbooru_latest,
                'options': {'pass_args': True},
                'args': ['page=PAGE_NUM', 'limit=LIMIT']
            }
        ]

        super(Danbooru, self).__init__()

    @run_async
    def danbooru_search(self, bot: Bot, update: Update, args: list = None):
        """Search on danbooru by tags command

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of search terms and options
        """
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        text = ' '.join(args)
        if not text:
            update.message.reply_text('You have to give me at least one tag.')
            return

        text, page = self.extract_option_from_string('page', text, int)
        text, limit = self.extract_option_from_string('limit', text, int)

        query = {
            'page': page or 0,
            'limit': limit or 10
        }

        terms = text.split(',')
        terms = self.filter_terms(terms)
        query['tags'] = ' '.join(terms[:2])

        if len(terms) > 2:
            update.message.reply_text('Only 2 tags per search supported, searching for {}'.format(query['tags']))

        self.post_list_send_media_group(bot, update, query)

    @run_async
    def danbooru_latest(self, bot: Bot, update: Update, args: list = None):
        """Danbooru show latest posts command

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): Various options see description
        """
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        text = ' '.join(args)
        text, page = self.extract_option_from_string('page', text, int)
        text, limit = self.extract_option_from_string('limit', text, int)

        query = {
            'page': page or 0,
            'limit': limit or 10
        }
        self.post_list_send_media_group(bot, update, query)

    def filter_terms(self, terms: list) -> list:
        """Ensure terms for the danbooru tag search are valid

        Args:
            terms (:obj:`list`): List of not yet validated strings

        Returns:
                :obj:`list`: List with the given strings validated
        """
        non_alphanum = re.compile('[^\w_ ]+')
        terms = map(lambda term: non_alphanum.sub('', term), terms)
        terms = map(lambda term: term.strip(), terms)
        terms = map(lambda term: term.replace(' ', '_'), terms)
        terms = filter(lambda term: not non_alphanum.match(term) and bool(term), terms)
        return list(OrderedDict.fromkeys(terms))

    def extract_option_from_string(self, name: str, text: str, type_: str or int = None) -> tuple:
        """Extract option from string

        Args:
            name (:obj:`str`): Name of the option
            text (:obj:`str`): Text itself
            type_ (:obj:`str` or :obj:`int`, optional): Type of option is it a string or an int, default is string

        Returns
            :obj:`tuple`: First item the text without the option, the second the value of the option
        """
        type_ = type_ or str
        options = {
            'name': name,
            'type': '\d' if type_ == int else '\w'
        }
        out = None

        page_pattern = re.compile('{name}[ =:]+{type}+'.format(**options), re.IGNORECASE)
        match = page_pattern.findall(text)
        if match:
            text = page_pattern.sub('', text)
            out = re.findall('\d+', match[0])[0]
            if type_ == int:
                out = int(re.findall('\d+', match[0])[0])

        return text, out

    def post_list_send_media_group(self, bot: Bot, update: Update, query: dict):
        """Perform :method:`pybooru.api_danbooru.DanbooruApi_Mixin#post_list` search and send found images to user as media group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            query (:obj:`dict`): Query with keywords for post_list see:
                https://pybooru.readthedocs.io/en/stable/api_danbooru.html#pybooru.api_danbooru.DanbooruApi_Mixin.post_list
        """
        if query.get('limit', 0) > 100:
            query['limit'] = 100

        client = PyDanbooru('danbooru', api_key=DANBOORU_API_TOKEN)
        posts = client.post_list(**query)

        if not posts:
            update.message.reply_text('Nothing found on page {page}'.format(**query))
            return

        errors = 0
        media_list = []
        for post in posts:
            image_url = post.get('large_file_url', post.get('source', None))

            if not image_url or not image_url.startswith('http'):
                errors += 1
                continue

            media_list.append(InputMediaPhoto(
                image_url, '{domain}/posts/{post_id}'.format(domain=client.site_url, post_id=post['id'])))

        while media_list:
            bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
            if len(media_list) > 1:
                try:
                    bot.send_media_group(
                        chat_id=update.message.chat_id,
                        media=media_list[:10],
                        reply_to_message_id=update.message.message_id,
                        disable_notification=True
                    )
                    del media_list[:10]
                except (BadRequest, TimedOut):
                    try:
                        update.message.reply_photo(
                            photo=media_list[0].media,
                            caption=media_list[0].caption,
                            disable_notification=True
                        )
                    except (BadRequest, TimedOut):
                        errors += 1
                    del media_list[0]
            else:
                try:
                    update.message.reply_photo(
                        photo=media_list[0].media,
                        caption=media_list[0].caption,
                        disable_notification=True
                    )
                except (BadRequest, TimedOut):
                    errors += 1
                del media_list[0]
        reply = ''
        if update.message.chat.type not in ['group', 'supergroup']:
            reply = 'Images has been sent'
            if errors:
                reply += ', but '

        if errors:
            reply += ('{} of the request {} are not publicly available'.format(errors, query['limit']))

        if reply:
            update.message.reply_text(reply)


danbooru = Danbooru()
