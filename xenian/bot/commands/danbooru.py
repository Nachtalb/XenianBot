import os
import re
from collections import OrderedDict

import requests
from pybooru import Danbooru as PyDanbooru
from requests.exceptions import MissingSchema
from requests_html import HTMLSession
from telegram import Bot, ChatAction, Update, InputMediaPhoto, InputFile
from telegram.error import BadRequest, TimedOut
from telegram.ext import run_async

from xenian.bot import mongodb_database
from xenian.bot.settings import DANBOORU_API_TOKEN, DANBOORU_LOGIN_PASSWORD, DANBOORU_LOGIN_USERNAME
from xenian.bot.utils import download_file_from_url_and_upload, TelegramProgressBar
from . import BaseCommand

__all__ = ['danbooru']


class Danbooru(BaseCommand):
    """The class for all danbooru related commands
    """
    group = 'Anime'

    FREE_LEVEL = 20
    GOLD_LEVEL = 30
    PLATINUM_LEVEL = 31
    BUILDER = 32
    JANITOR = 35
    MODERATOR = 40
    ADMIN = 50

    level_restrictions = {
        'tag_limit': {
            FREE_LEVEL: 2,
            GOLD_LEVEL: 6,
            PLATINUM_LEVEL: 12,
            BUILDER: 32,
            JANITOR: 35,
            MODERATOR: 40,
            ADMIN: 50,
        },
        'censored_tags': {
            FREE_LEVEL: True,
            GOLD_LEVEL: False,
            PLATINUM_LEVEL: False,
            BUILDER: False,
            JANITOR: False,
            MODERATOR: False,
            ADMIN: False,
        }
    }

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
                'description': 'Get latest uploads from danbooru you can use the options page (default 0), limit '
                               '(default 10, max 100) and group (default 0)',
                'command': self.danbooru_latest,
                'options': {'pass_args': True},
                'args': ['page=PAGE_NUM', 'limit=LIMIT, group=SIZE']
            }
        ]

        if DANBOORU_API_TOKEN:
            if not DANBOORU_LOGIN_USERNAME:
                raise ValueError('When Danbooru API kay is set, username must also be.')
            self.client = PyDanbooru('danbooru', username=DANBOORU_LOGIN_USERNAME, api_key=DANBOORU_API_TOKEN)
        else:
            self.client = PyDanbooru('danbooru')

        self.user_level = 20
        if DANBOORU_LOGIN_USERNAME:
            user = self.client.user_list(name_matches=self.client.username)
            self.user_level = user[0]['level']

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

        self.files = mongodb_database.files

        super(Danbooru, self).__init__()

    @run_async
    def danbooru_search(self, bot: Bot, update: Update, args: list = None):
        """Search on danbooru by tags command

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of search terms and options
        """
        message = update.message
        text = ' '.join(args)
        if not text:
            update.message.reply_text('You have to give me at least one tag.')
            return

        text, page = self.extract_option_from_string('page', text, int)
        text, limit = self.extract_option_from_string('limit', text, int)
        text, group_size = self.extract_option_from_string('group', text, int)

        if group_size and group_size > 10:
            message.reply_text('Max group size is 10', reply_to_message_id=message.message_id)
            return

        query = {
            'page': page or 0,
            'limit': limit or 10
        }

        if ',' in text:
            terms = text.split(',')
        else:
            terms = text.split(' ')
        terms = self.filter_terms(terms)

        tag_limit = self.level_restrictions['tag_limit'][self.user_level]
        if len(terms) > tag_limit:
            message.reply_text(f'Only {tag_limit} tags can be used.', reply_to_message_id=message.message_id)
            return
        if self.level_restrictions['censored_tags'][self.user_level]:
            message.reply_text('Some tags may be censored', reply_to_message_id=message.message_id)

        query['tags'] = ' '.join(terms)

        self.post_list_send_media_group(bot, update, query, group_size=group_size)

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
        black_list = re.compile('[^\w_\- +~*:]+')
        terms = map(lambda term: black_list.sub('', term), terms)
        terms = map(lambda term: term.strip(), terms)
        terms = map(lambda term: term.replace(' ', '_'), terms)
        terms = filter(lambda term: not black_list.match(term) and bool(term), terms)
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

    def get_image(self, post_id: int, image_url: str = None):
        """Save image to file and save in db

        Args:
            post_id (:obj:`int`): Post od as identification
            image_url (:obj:`str`, optional): Url to image which should be saved

        Returns:
           ( :obj:`str`): Location of saved file
        """
        db_entry = self.files.find_one({'file_id': post_id})
        if db_entry:
            location = db_entry['location']
            if os.path.isfile(location):
                return location

            try:
                response = requests.head(location)
                if response.status_code == 200:
                    return location
            except MissingSchema:
                # This gets raised when a "location" is a local file but does not exist anymore
                pass

        if not image_url:
            return

        downloaded_image_location = download_file_from_url_and_upload(image_url)
        self.files.update({'file_id': post_id},
                          {'file_id': post_id, 'location': downloaded_image_location},
                          upsert=True)
        return downloaded_image_location

    def post_list_send_media_group(self, bot: Bot, update: Update, query: dict, group_size: bool = False):
        """Perform :method:`pybooru.api_danbooru.DanbooruApi_Mixin#post_list` search and send found images to user as media group

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            query (:obj:`dict`): Query with keywords for post_list see:
                https://pybooru.readthedocs.io/en/stable/api_danbooru.html#pybooru.api_danbooru.DanbooruApi_Mixin.post_list
            group_size (:obj:`bool`): If the found items shall be grouped to a media group
        """
        if query.get('limit', 0) > 100:
            query['limit'] = 100

        posts = self.client.post_list(**query)

        if not posts:
            update.message.reply_text('Nothing found on page {page}'.format(**query))
            return

        progress_bar = TelegramProgressBar(
            bot=bot,
            chat_id=update.message.chat_id,
            pre_message=('Sending' if not group_size else 'Gathering') + ' files\n{current} / {total}',
            se_message='This could take some time.'
        )

        groups = {}
        current_group_index = 0
        error = False
        for index, post in progress_bar.enumerate(posts):
            image_url = post.get('large_file_url', None)
            post_url = '{domain}/posts/{post_id}'.format(domain=self.client.site_url, post_id=post['id'])
            post_id = post['id']
            caption = f'@XenianBot - {post_url}'

            image_url = self.get_image(post_id, image_url) or image_url

            if not image_url:
                if self.logged_in_session or group_size:
                    response = self.logged_in_session.get(post_url)
                    img_tag = response.html.find('#image-container > img')

                    if not img_tag:
                        error = True
                        continue
                    img_tag = img_tag[0]
                    image_url = self.get_image(post_id, img_tag.attrs['src'])
                else:
                    image_url = post.get('source', None)

            if not image_url:
                error = True
                continue

            if group_size:
                if index % group_size == 0:
                    current_group_index += 1
                groups.setdefault(current_group_index, [])
                groups[current_group_index].append(InputMediaPhoto(image_url, caption))
                continue

            bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
            try:
                file = None
                if os.path.isfile(image_url):
                    file = open(image_url, mode='rb')

                sent_photo = update.message.reply_photo(
                    photo=file or image_url,
                    caption=caption,
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

        for group_index, items in groups.items():
            for item in items:
                with open(item.media, 'rb') as file_:
                    item.media = InputFile(file_, attach=True)

            bot.send_media_group(
                chat_id=update.message.chat_id,
                media=items,
                reply_to_message_id=update.message.message_id,
                disable_notification=True
            )

        reply = ''
        if update.message.chat.type not in ['group', 'supergroup']:
            reply = 'Images has been sent'

        if error:
            reply += '\nNot all found images could be sent. Most of the times this is because an image is not ' \
                     'publicly available.'
        if reply:
            update.message.reply_text(reply.strip())


danbooru = Danbooru()
