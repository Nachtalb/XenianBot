import os
import re
from collections import OrderedDict
from copy import deepcopy
from typing import Callable, Iterable

import requests
from pybooru import Danbooru as PyDanbooru, Moebooru as PyMoebooru
from pybooru.resources import SITE_LIST
from requests.exceptions import MissingSchema
from requests_html import HTMLSession
from telegram import Bot, ChatAction, InputFile, InputMediaPhoto, Message, Update
from telegram.error import BadRequest, NetworkError, TimedOut
from telegram.ext import run_async

from xenian.bot import mongodb_database
from xenian.bot.settings import ANIME_SERVICES
from xenian.bot.utils import TelegramProgressBar, download_file_from_url_and_upload
from xenian.bot.utils.telegram import retry_command
from . import BaseCommand

__all__ = ['animedatabases']

SITE_LIST['safebooru'] = {'url': 'https://safebooru.donmai.us'}


class BaseService:
    type = 'base'

    def __init__(self, name: str, url: str, api: str = None, username: str = None, password: str = None):
        self.name = name
        self.url = url.lstrip('/') if url is not None else None
        self.api = api
        self.username = username
        self.password = password

        self.count_qualifiers_as_tag = False
        self.client = None
        self.session = None
        self.tag_limit = None
        self.censored_tags = None

    def init_client(self):
        raise NotImplemented

    def init_session(self):
        raise NotImplemented


class DanbooruService(BaseService):
    FREE_LEVEL = 20
    GOLD_LEVEL = 30
    PLATINUM_LEVEL = 31
    BUILDER = 32
    JANITOR = 35
    MODERATOR = 40
    ADMIN = 50

    LEVEL_RESTRICTIONS = {
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

    type = 'danbooru'

    def __init__(self, name: str, url: str, api: str = None, username: str = None, password: str = None) -> None:
        super(DanbooruService, self).__init__(name=name, url=url, api=api, username=username, password=password)
        self.user_level = None

        self.init_client()
        self.init_session()

    def init_client(self):
        if self.api:
            if not self.username:
                raise ValueError('Danbooru API Services need a Username when API key is given.')
            self.client = PyDanbooru(site_name=self.name, site_url=self.url, api_key=self.api, username=self.username)
        else:
            self.client = PyDanbooru(site_name=self.name, site_url=self.url)

        self.user_level = self.get_user_level()
        self.tag_limit = self.LEVEL_RESTRICTIONS['tag_limit'][self.user_level]
        self.censored_tags = self.LEVEL_RESTRICTIONS['censored_tags'][self.user_level]

        if not self.url:
            self.url = self.client.site_url.lstrip('/')

    def init_session(self):
        if self.username and self.password and self.url:
            self.session = HTMLSession()
            login_page = self.session.get(f'{self.url.lstrip("/")}/session/new')
            form = login_page.html.find('.simple_form')[0]

            login_data = {
                'name': self.username,
                'password': self.password,
                'remember': '1',
            }
            for input in form.find('input'):
                value = input.attrs.get('value', None)
                name = input.attrs.get('name', None)
                if name:
                    login_data.setdefault(name, value)

            self.session.post(f'{self.url.lstrip("/")}/session', login_data)

    def get_user_level(self):
        user_level = 20
        if self.username:
            user = self.client.user_list(name_matches=self.client.username)
            user_level = user[0]['level']
        return user_level


class MoebooruService(BaseService):
    type = 'moebooru'

    def __init__(self, name: str, url: str, username: str = None, password: str = None,
                 hashed_string: str = None) -> None:
        super(MoebooruService, self).__init__(name=name, url=url, username=username, password=password)
        self.tag_limit = 6
        self.hashed_string = hashed_string
        self.count_qualifiers_as_tag = True

        self.init_client()

    def init_client(self):
        if self.username and self.password:
            self.client = PyMoebooru(site_name=self.name, site_url=self.url, hash_string=self.hashed_string,
                                     username=self.username, password=self.password)
            return

        self.client = PyMoebooru(site_name=self.name, site_url=self.url)
        if not self.url:
            self.url = self.client.site_url.lstrip('/')


class SendError:
    IMAGE_NOT_FOUND = 0
    WRONG_FILE_TYPE = 10
    UNDEFINED_ERROR = 20

    def __init__(self, code: int, post: dict = None, image: InputMediaPhoto = None, post_url: str = None):
        self.code = code
        self.post = post
        self.image = image
        self.post_url = post_url


class MessageQueue:
    tag_limit = 6

    def __init__(self, total: int, message: Message, group_size: int = None):
        self.total = total
        self.message = message
        self.group_size = group_size or 1

        self.sent = 0
        self.errors = []

    def report(self, error: SendError = None):
        if error:
            self.errors.append(error)

        self.sent += 1
        if self.sent == self.total:
            self.finished()

    def finished(self):
        lines = []
        if self.message.chat.type not in ['group', 'supergroup']:
            lines.append('Images has been sent')

        if self.errors:
            error_codes = set(error.code for error in self.errors)
            if SendError.IMAGE_NOT_FOUND in error_codes:
                lines.append('Some files could not be retrieved')
                for error in filter(lambda e: e.code == SendError.IMAGE_NOT_FOUND and e.post_url, self.errors):
                    lines.append(f'- {error.post_url}')

            if SendError.WRONG_FILE_TYPE in error_codes and self.group_size > 1:
                lines.append('Videos were skipped because they cannot be sent via a group.')
                for error in filter(lambda e: e.code == SendError.WRONG_FILE_TYPE and e.post_url, self.errors):
                    lines.append(f'- {error.post_url}')

            if SendError.UNDEFINED_ERROR in error_codes:
                lines.append('Some files could not be sent')

        if lines:
            self.message.reply_text('\n'.join(lines),
                                    reply_to_message_id=self.message.message_id,
                                    disable_web_page_preview=True)

    @staticmethod
    def message_queue_exc_handler(argument_name: str):
        def wrapper(func, *args, **kwargs):
            def inner_wrapper(*args, **kwargs):
                queue = kwargs.get(argument_name)
                if not queue:
                    queues = [arg for arg in args if isinstance(arg, MessageQueue)]
                    if len(queues) > 1:
                        raise AttributeError('Got more than one MessageQueue\'s')
                    elif queues:
                        queue = queues[0]
                if not queue:
                    raise AttributeError('No MessageQueue found')
                try:
                    return func(*args, **kwargs)
                except (BadRequest, TimedOut, NetworkError) as e:
                    if isinstance(e, NetworkError) and 'The write operation timed out' not in e.message:
                        raise e

                    for item in range(queue.group_size):
                        queue.report(SendError(code=SendError.UNDEFINED_ERROR))

            return inner_wrapper

        return wrapper


class AnimeDatabases(BaseCommand):
    """The class for all danbooru related commands
    """
    group = 'Anime'

    def __init__(self):
        self.files = mongodb_database.files

        self.services = {}
        self.init_services()

        super(AnimeDatabases, self).__init__()

    def init_services(self):
        """Initialize services
        """
        for service in ANIME_SERVICES:
            name = service['name']
            service_information = deepcopy(service)
            del service_information['type']
            if service['type'] == 'danbooru':
                self.services[name] = DanbooruService(**service_information)
            if service['type'] == 'moebooru':
                self.services[name] = MoebooruService(**service_information)

            self.commands.append({
                'title': name.capitalize(),
                'description': f'Search on {name}',
                'command': self.search_wrapper(name),
                'command_name': name,
                'options': {'pass_args': True},
                'args': ['tag1', 'tag2...', 'page=PAGE_NUM', 'limit=LIMIT', 'group=SIZE']
            })

    def search_wrapper(self, service_name: str) -> Callable:
        """Wrapper to set the service for the search command

        Args:
            service_name (:obj:`str`): Name for the service

        Returns:
            (:obj:`Callable`): Search method for the telegram command

        Raises:
            (:class:`NotImplementedError`): Search function for given service does not exist
        """
        service = self.services[service_name]

        method_name = f'{service.type}_search'
        method = getattr(self, method_name, None)

        if not method:
            method = self.search

        def search(*args, **kwargs):
            method(service=service, *args, **kwargs)

        return search

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

    @run_async
    def search(self, bot: Bot, update: Update, service: BaseService, args: list = None):
        """Generic search based on :class:`BaseService`

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            service (:obj:`BaseService`): Initialized :obj:`BaseService` for the various api calls
            args (:obj:`list`, optional): List of search terms and options
        """
        message = update.message
        text = ' '.join(args)

        text, page = self.extract_option_from_string('page', text, int)
        text, limit = self.extract_option_from_string('limit', text, int)
        text, group_size = self.extract_option_from_string('group', text, int)

        if group_size and group_size > 10:
            message.reply_text('Max group size is 10', reply_to_message_id=message.message_id)
            return

        if ',' in text:
            terms = text.split(',')
        else:
            terms = text.split(' ')
        terms = self.filter_terms(terms)

        actual_tags = [term for term in terms if ':' not in term]  # Qualifiers like "order:score" are not tags
        if service.count_qualifiers_as_tag:
            actual_tags = terms

        if service.tag_limit and len(actual_tags) > service.tag_limit:
            message.reply_text(f'Only {service.tag_limit} tags can be used.', reply_to_message_id=message.message_id)
            return

        if service.censored_tags:
            message.reply_text('Some tags may be censored', reply_to_message_id=message.message_id)

        query = {
            'page': page or 0,
            'limit': limit if limit and limit <= 100 else 10,
            'tags': ' '.join(terms),
        }

        method_name = f'{service.type}_real_search'
        method = getattr(self, method_name, None)

        if not method:
            raise NotImplementedError(f'Search function ({method_name}) for service {service.name} does not exist.')

        method(bot=bot, update=update, service=service, query=query, group_size=group_size)

    @run_async
    @retry_command
    @MessageQueue.message_queue_exc_handler('queue')
    def send_group(self, bot: Bot, update: Update, group: Iterable[InputMediaPhoto], queue: MessageQueue):
        for item in group:
            if os.path.isfile(item.media):
                with open(item.media, 'rb') as file_:
                    item.media = InputFile(file_, attach=True)

        message = update.message
        bot.send_media_group(
            chat_id=message.chat_id,
            media=group,
            reply_to_message_id=message.message_id,
            disable_notification=True
        )
        for image in group:
            queue.report()

    @run_async
    @MessageQueue.message_queue_exc_handler('queue')
    @retry_command
    def send_image(self, update: Update, image: InputMediaPhoto, queue: MessageQueue):
        file = None
        message = update.message
        if os.path.isfile(image.media):
            file = open(image.media, mode='rb')

        sent_media = None
        if image.media.endswith(('.png', '.jpg')):
            sent_media = message.reply_photo(
                photo=file or image.media,
                caption=image.caption,
                disable_notification=True,
                reply_to_message_id=message.message_id,
            )

        if file:
            file.seek(0)

        message.chat.send_document(
            document=file or image.media,
            disable_notification=True,
            caption=image.caption,
            reply_to_message_id=sent_media.message_id if sent_media else None,
        )
        queue.report()

    # Danbooru API commands

    def danbooru_real_search(self, bot: Bot, update: Update, service: DanbooruService, query: dict,
                             group_size: bool = False):
        """Send Danbooru API Service queried images to user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            query (:obj:`dict`): Query with keywords for post_list see:
                https://pybooru.readthedocs.io/en/stable/api_danbooru.html#pybooru.api_danbooru.DanbooruApi_Mixin.post_list
            group_size (:obj:`bool`): If the found items shall be grouped to a media group
        """
        message = update.message
        posts = service.client.post_list(**query)

        if not posts:
            message.reply_text('Nothing found on page {page}'.format(**query))
            return

        progress_bar = TelegramProgressBar(
            bot=bot,
            chat_id=message.chat_id,
            pre_message=('Sending' if not group_size else 'Gathering') + ' files\n{current} / {total}',
            se_message='This could take some time.'
        )

        message_queue = MessageQueue(total=len(posts), message=message, group_size=group_size)

        group = []
        for index, post in progress_bar.enumerate(posts):
            image_url = post.get('large_file_url', None)
            post_url = '{domain}/posts/{post_id}'.format(domain=service.url, post_id=post['id'])
            post_id = post['id']
            caption = f'@XenianBot - {post_url}'

            image_url = self.get_image(post_id, image_url) or image_url

            if not image_url:
                if service.session or group_size:
                    response = service.session.get(post_url)
                    img_tag = response.html.find('#image-container > img')

                    if img_tag:
                        img_tag = img_tag[0]
                        image_url = self.get_image(post_id, img_tag.attrs['src'])

            if not image_url:
                message_queue.report(SendError(code=SendError.IMAGE_NOT_FOUND, post=post, post_url=post_url))
                continue
            image = InputMediaPhoto(image_url, caption)
            if group_size:
                if image_url.endswith(('.webm', '.gif', '.mp4', '.swf', '.zip')):
                    message_queue.report(SendError(code=SendError.WRONG_FILE_TYPE, post=post, post_url=post_url))
                    continue
                if index and index % group_size == 0:
                    self.send_group(group=group, bot=bot, update=update, queue=message_queue)
                    group = []
                group.append(image)
                continue

            bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_PHOTO)
            self.send_image(update=update, image=image, queue=message_queue)

        if group:
            self.send_group(group=group, bot=bot, update=update, queue=message_queue)

    # Moebooru API commands

    def moebooru_real_search(self, bot: Bot, update: Update, service: MoebooruService, query: dict,
                             group_size: bool = False):
        message = update.message
        posts = service.client.post_list(**query)

        if not posts:
            message.reply_text('Nothing found on page {page}'.format(**query))
            return

        progress_bar = TelegramProgressBar(
            bot=bot,
            chat_id=message.chat_id,
            pre_message=('Sending' if not group_size else 'Gathering') + ' files\n{current} / {total}',
            se_message='This could take some time.'
        )

        message_queue = MessageQueue(total=len(posts), message=message, group_size=group_size)

        group = []
        for index, post in progress_bar.enumerate(posts):
            post_url = '{domain}/posts/{post_id}'.format(domain=service.url, post_id=post['id'])

            image = InputMediaPhoto(post['file_url'], f'@XenianBot - {post_url}')

            if group_size:
                if image.media.endswith(('.webm', '.gif', '.mp4', '.swf', '.zip')):
                    message_queue.report(SendError(code=SendError.WRONG_FILE_TYPE, post=post, post_url=post_url))
                    continue
                if index and index % group_size == 0:
                    self.send_group(group=group, bot=bot, update=update, queue=message_queue)
                    group = []
                group.append(image)
                continue
            else:
                self.send_image(update=update, image=image, queue=message_queue)

        if group:
            self.send_group(group=group, bot=bot, update=update, queue=message_queue)


animedatabases = AnimeDatabases()
