import re
from collections import OrderedDict

from pybooru import Danbooru
from telegram import Bot, ChatAction, InputMediaPhoto, Update
from telegram.ext import run_async

from . import BaseCommand

__all__ = ['danbooru_search_tags', 'danbooru_latest']


class DanbooruMixims:

    def filter_terms(self, terms: list):
        """Filter terms by removing non alphanumeric and duplicates

        Args:
            terms (:obj:`list`): List of strings
        """
        non_alphanum = re.compile('[^\w_ ]+')
        terms = map(lambda term: non_alphanum.sub('', term), terms)
        terms = map(lambda term: term.strip(), terms)
        terms = map(lambda term: term.replace(' ', '_'), terms)
        terms = filter(lambda term: not non_alphanum.match(term) and bool(term), terms)
        return list(OrderedDict.fromkeys(terms))

    def extract_option_from_string(self, name: str, text: str, type_: str or int = None):
        """Extract option from string

        Args:
            name (:obj:`str`): Name of the option
            text (:obj:`str`): Text itself
            type_ (:obj:`str` or :obj:`int`): Type of option is it a string or an int, default is string

        Returns
            (:obj:`tuple`): First item the text without the option, the second the value of the option
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
        """Perform client.post_list search and send found images to user as media group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            query (:obj:`dict`): Query with keywords for post_list see:
                https://pybooru.readthedocs.io/en/stable/api_danbooru.html#pybooru.api_danbooru.DanbooruApi_Mixin.post_list
        """
        if query.get('limit', 0) > 100:
            query['limit'] = 100

        client = Danbooru('danbooru')
        posts = client.post_list(**query)

        if not posts:
            update.message.reply_text('Nothing found on page {page}'.format(**query))
            return

        media_list = []
        for post in posts:
            image_url = post.get('large_file_url', None)
            image_url = client.site_url + image_url if image_url else post['source']

            media_list.append(InputMediaPhoto(
                image_url, '{domain}/posts/{post_id}'.format(domain=client.site_url, post_id=post['id'])))

        while media_list:
            bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
            if len(media_list) > 1:
                bot.send_media_group(
                    chat_id=update.message.chat_id,
                    media=media_list[:10],
                    reply_to_message_id=update.message.message_id
                )
                del media_list[:10]
            else:
                bot.send_photo(
                    chat_id=update.message.chat_id,
                    photo=media_list[0].media,
                    caption=media_list[0].caption)
                del media_list[0]


class DanbooruSearch(DanbooruMixims, BaseCommand):
    command_name = 'danbooru_tags'
    title = 'Danobooru Search'
    description = 'Search on danbooru by max 2 tags separated by comma. You can define which page (default 0) and the' \
                  ' limit (default 5, max 100)'
    args = '2_TAGS page=PAGE_NUM limit=LIMIT'

    def __init__(self):
        super(DanbooruSearch, self).__init__()
        self.options['pass_args'] = True

    @run_async
    def command(self, bot: Bot, update: Update, args: list = None):
        """Search on danbooru by tags

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of search terms and options
        """
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        query = {
            'limit': 5,
            'page': 0
        }

        text = ' '.join(args)
        if not text:
            update.message.reply_text('You have to give me at least one tag.')
            return

        text, page = self.extract_option_from_string('page', text, int)
        text, limit = self.extract_option_from_string('limit', text, int)

        if page:
            query['page'] = page
        if limit:
            query['limit'] = limit

        terms = text.split(',')
        terms = self.filter_terms(terms)
        query['tags'] = ' '.join(terms[:2])

        if len(terms) > 2:
            update.message.reply_text('Only 2 tags per search supported, searching for {}'.format(query['tags']))

        self.post_list_send_media_group(bot, update, query)


danbooru_search_tags = DanbooruSearch()


class DanbooruLatest(DanbooruMixims, BaseCommand):
    command_name = 'danbooru_latest'
    title = 'Danobooru Latest'
    description = 'Get latest uploads from danbooru you can use the options page (default 0) and limit (default 5, ' \
                  'max 100)'
    args = 'page=PAGE_NUM limit=LIMIT'

    def __init__(self):
        super(DanbooruLatest, self).__init__()
        self.options['pass_args'] = True

    @run_async
    def command(self, bot: Bot, update: Update, args: list = None):
        """Danbooru latest posts

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): Various options see description
        """
        bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

        query = {
            'limit': 5,
            'page': 0
        }

        text = ' '.join(args)
        text, page = self.extract_option_from_string('page', text, int)
        text, limit = self.extract_option_from_string('limit', text, int)

        if page:
            query['page'] = page
        if limit:
            query['limit'] = limit

        self.post_list_send_media_group(bot, update, query)


danbooru_latest = DanbooruLatest()
