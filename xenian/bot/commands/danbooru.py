import os
import re
from collections import OrderedDict

from pybooru import Danbooru as PyDanbooru
from requests_html import HTMLSession
from telegram import Bot, ChatAction, Update
from telegram.error import BadRequest, TimedOut
from telegram.ext import run_async

from xenian.bot.settings import DANBOORU_API_TOKEN, DANBOORU_LOGIN_PASSWORD, DANBOORU_LOGIN_USERNAME
from xenian.bot.utils import download_file_from_url_and_upload
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

        self.logged_in_session = None
        if DANBOORU_LOGIN_USERNAME and DANBOORU_LOGIN_PASSWORD:
            self.logged_in_session = HTMLSession()
            login_page = self.logged_in_session.get('https://danbooru.donmai.us/session/new')
            form = login_page.html.find('.simple_form')[0]

            login_data = {
                'name': DANBOORU_LOGIN_USERNAME,
                'password': DANBOORU_LOGIN_PASSWORD,
                'remember': '1',
            }
            for input in form.find('input'):
                value = input.attrs.get('value', None)
                name = input.attrs.get('name', None)
                if name:
                    login_data.setdefault(name, value)

            self.logged_in_session.post('https://danbooru.donmai.us/session', login_data)

        super(Danbooru, self).__init__()

    @run_async
    def danbooru_search(self, bot: Bot, update: Update, args: list = None):
        """Search on danbooru by tags command

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of search terms and options
        """
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

        if ',' in text:
            terms = text.split(',')
        else:
            terms = text.split(' ')
        terms = self.filter_terms(terms)
        query['tags'] = ' '.join(terms[:2])

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

        error = False
        for post in posts:
            image_url = post.get('large_file_url', None)
            post_url = '{domain}/posts/{post_id}'.format(domain=client.site_url, post_id=post['id'])
            if not image_url:
                if self.logged_in_session:
                    response = self.logged_in_session.get(post_url)
                    img_tag = response.html.find('#image-container > img')

                    if not img_tag:
                        error = True
                        continue
                    img_tag = img_tag[0]
                    image_url = download_file_from_url_and_upload(img_tag.attrs['src'])
                else:
                    image_url = post.get('source', None)

            if not image_url:
                error = True
                continue

            bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
            try:
                file = None
                if os.path.isfile(image_url):
                    file = open(image_url, mode='rb')

                sent_photo = update.message.reply_photo(
                    photo=file or image_url,
                    caption=post_url,
                    disable_notification=True,
                    reply_to_message_id=update.message.message_id,
                )

                if file:
                    file.seek(0)
                sent_photo.reply_document(
                    document=file or image_url,
                    disable_notification=True,
                    reply_to_message_id=sent_photo.message_id,
                )
            except (BadRequest, TimedOut):
                error = True
                continue

        reply = ''
        if update.message.chat.type not in ['group', 'supergroup']:
            reply = 'Images has been sent'

        if error:
            reply += '\nNot all found images could be sent. Most of the times this is because an image is not ' \
                     'publicly available.'
        if reply:
            update.message.reply_text(reply.strip())


danbooru = Danbooru()
