import json
import os
import re
import zipfile
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable, Iterable

import requests
from requests.exceptions import MissingSchema
from telegram import Bot, ChatAction, InputFile, InputMediaPhoto, Update
from telegram.ext import run_async

from xenian.bot import mongodb_database
from xenian.bot.commands.animedatabase_utils.base_service import BaseService
from xenian.bot.commands.animedatabase_utils.danbooru_service import DanbooruService
from xenian.bot.commands.animedatabase_utils.message_queue import MessageQueue
from xenian.bot.commands.animedatabase_utils.moebooru_service import MoebooruService
from xenian.bot.commands.animedatabase_utils.post import Post, PostError
from xenian.bot.settings import ANIME_SERVICES
from xenian.bot.utils import CustomNamedTemporaryFile, TelegramProgressBar, download_file_from_url_and_upload
from xenian.bot.utils.telegram import retry_command
from . import BaseCommand

__all__ = ['animedatabases']


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

    def extract_option_from_string(self, name: str, text: str, type_: str or int = None, default: Any = None) -> tuple:
        """Extract option from string

        Args:
            name (:obj:`str`): Name of the option
            text (:obj:`str`): Text itself
            type_ (:obj:`str` or :obj:`int`, optional): Type of option is it a string or an int, default is string
            default (:obj:`any`, optional): Default value to return if `name` was not found in `text`

        Returns
            :obj:`tuple`: First item the text without the option, the second the value of the option
        """
        if type_ is bool:
            if name in text:
                text = text.replace(name, '', 1)
                return text, not bool(default)
            return text, bool(default)

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

        return text, out if out is not None else default

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
        text, zip_it = self.extract_option_from_string('zip', text, bool)
        text, limit = self.extract_option_from_string('limit', text, int)
        text, group_size = self.extract_option_from_string('group', text, int, default=10)
        group_size = group_size or None

        if group_size and group_size > 10:
            message.reply_text('Max group size is 10, use default (10)', reply_to_message_id=message.message_id)
            group_size = 10

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

        method(bot=bot, update=update, service=service, query=query, group_size=group_size, zip_it=zip_it)

    @run_async
    @MessageQueue.message_queue_exc_handler('queue')
    @retry_command
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

    @run_async
    @retry_command
    def send_zip(self, update: Update, posts=Iterable[Post]):
        with CustomNamedTemporaryFile(prefix='xenian-', suffix='.zip') as zip_file:
            zip = zipfile.ZipFile(zip_file.name, mode='w')

            text_file_content = ''
            for post in posts:
                if os.path.isfile(post.media):
                    filename = os.path.basename(str(post.post['id']) + os.path.splitext(post.media)[1])
                    json_filename = filename + '.json'
                    zip.write(post.media, filename)
                    text_file_content += f'{filename} ({filename}.json) -> {post.post_url}\n'

                    with CustomNamedTemporaryFile(mode='w') as json_file:
                        json.dump(post.post, json_file, indent=4, sort_keys=True)
                        json_file.close()
                        zip.write(json_file.name, json_filename)

            with CustomNamedTemporaryFile(mode='w') as text_file:
                text_file.write(text_file_content)
                text_file.close()
                zip.write(text_file.name, 'Links.txt')

            zip.close()

            update.message.chat.send_document(
                document=zip_file,
                reply_to_message_id=update.message.message_id,
            )

    # Danbooru API commands

    def danbooru_get_image(self, post: dict, service: DanbooruService) -> Post:
        image_url = post.get('large_file_url', None)
        post_url = '{domain}/posts/{post_id}'.format(domain=service.url, post_id=post['id'])

        image_url = self.get_image(post['id'], image_url) or image_url

        if not image_url and service.session:
            response = service.session.get(post_url)
            img_tag = response.html.find('#image-container > img')

            if img_tag:
                img_tag = img_tag[0]
                image_url = self.get_image(post['id'], img_tag.attrs['src'])

        if not image_url:
            raise PostError(code=PostError.IMAGE_NOT_FOUND, post=Post(post=post, post_url=post_url))

        return Post(post, media=image_url, caption=f'@XenianBot - {post_url}', post_url=post_url)

    def danbooru_real_search(self, bot: Bot, update: Update, service: DanbooruService, query: dict,
                             group_size: bool = False, zip_it: bool = False):
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
            pre_message=('Gathering' if group_size or zip_it else 'Sending') + ' files\n{current} / {total}',
            se_message='This could take some time.'
        )

        message_queue = MessageQueue(total=len(posts), message=message, group_size=group_size)

        parsed_posts = []
        group = []
        for index, post_dict in progress_bar.enumerate(posts):
            try:
                post = self.danbooru_get_image(post=post_dict, service=service)
                parsed_posts.append(post)
            except PostError as error:
                message_queue.report(error)
                continue

            if zip_it:
                continue

            if group_size:
                if post.is_video():
                    message_queue.report(PostError(code=PostError.WRONG_FILE_TYPE, post=post))
                    continue
                if index and index % group_size == 0:
                    self.send_group(group=group, bot=bot, update=update, queue=message_queue)
                    group = []
                group.append(post.telegram)
                continue

            bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_PHOTO)
            self.send_image(update=update, image=post.telegram, queue=message_queue)

        if zip_it:
            self.send_zip(update=update, posts=parsed_posts)
            return

        if group:
            self.send_group(group=group, bot=bot, update=update, queue=message_queue)

    # Moebooru API commands

    def moebooru_get_image(self, post: dict, service: MoebooruService, download: bool = False) -> Post:
        post_url = '{domain}/posts/{post_id}'.format(domain=service.url, post_id=post['id'])
        image_path = post['file_url']

        if download:
            image_path = self.get_image(post['id'], post['file_url'])

        return Post(post=post, media=image_path, caption=f'@XenianBot - {post_url}', post_url=post_url)

    def moebooru_real_search(self, bot: Bot, update: Update, service: MoebooruService, query: dict,
                             group_size: bool = False, zip_it: bool = False):
        message = update.message
        posts = service.client.post_list(**query)

        if not posts:
            message.reply_text('Nothing found on page {page}'.format(**query))
            return

        progress_bar = TelegramProgressBar(
            bot=bot,
            chat_id=message.chat_id,
            pre_message=('Gathering' if group_size or zip_it else 'Sending') + ' files\n{current} / {total}',
            se_message='This could take some time.'
        )

        message_queue = MessageQueue(total=len(posts), message=message, group_size=group_size)

        group = []
        parsed_posts = []
        for index, post_dict in progress_bar.enumerate(posts):
            post = self.moebooru_get_image(post=post_dict, service=service, download=zip_it)
            parsed_posts.append(post)

            if zip_it:
                continue

            if group_size:
                if post.is_video():
                    message_queue.report(PostError(code=PostError.WRONG_FILE_TYPE, post=post))
                    continue
                if index and index % group_size == 0:
                    self.send_group(group=group, bot=bot, update=update, queue=message_queue)
                    group = []
                group.append(post.telegram)
                continue
            else:
                self.send_image(update=update, image=post.telegram, queue=message_queue)

        if zip_it:
            self.send_zip(update=update, posts=parsed_posts)
            return

        if group:
            self.send_group(group=group, bot=bot, update=update, queue=message_queue)


animedatabases = AnimeDatabases()
