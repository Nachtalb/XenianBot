import os
import re
from contextlib import contextmanager
from tempfile import TemporaryDirectory

import requests
from instaLooter import InstaLooter
from telegram import Bot, ChatAction, InputMediaPhoto, InputMediaVideo, MessageEntity, Update
from telegram.ext import Filters, MessageHandler, run_async, BaseFilter

from xenian_bot.commands.filters.download_mode import download_mode_filter
from xenian_bot.utils import data
from . import BaseCommand

__all__ = ['instagram']


class Instagram(BaseCommand):
    """Instagram Downloader integration for this bot


    Attributes:
        data_name (:obj:`str`): The name for the data set where the user credentials are saved
        base_url (:obj:`str`): Base URL of Instagram
        link_pattern (:obj:`_sre.SRE_Pattern`): A regex compiled string which matches any Instagram link
    """
    data_name = 'instagram'
    base_url = 'instagram.com'
    link_pattern = re.compile('^((http(s)?:)?//)?(www\.)?{}'.format(base_url.replace('.', '\.')))

    def __init__(self):
        self.commands = [
            {
                'title': 'Instagram Profile Download',
                'description': 'Download a all posts from an user',
                'args': 'POST_LINK OR POST_ID',
                'command': self.insta,
                'options': {'pass_args': True}
            },
            {
                'title': 'Instagram Post Download',
                'description': 'Download a post from Instagram via its link or its PostID',
                'args': 'PROFILE_LINK OR USERNAME',
                'command': self.instap,
                'options': {'pass_args': True}
            },
            {
                'title': 'Instagram Login',
                'description': 'Login to Instagram, does not work in groups for security.',
                'args': 'USERNAME PASSWORD',
                'command': self.instali,
                'options': {'pass_args': True, 'filters': ~ Filters.group}
            },
            {
                'title': 'Instagram Logout',
                'description': 'Logout from Instagram',
                'command': self.instalo,
            },
            {
                'title': 'Instagram Auto Link',
                'description': 'Turn on /download_mode and send links to Instargam posts to auto-download them',
                'command': self.insta_link_auto,
                'handler': MessageHandler,
                'options': {
                    'filters': Filters.entity(MessageEntity.URL) & download_mode_filter & Instagram.insta_link_filter()
                },
            }
        ]

        super(Instagram, self).__init__()

    @staticmethod
    def insta_link_filter():
        """Small filter to test against Instagram URLs

        Returns:
            :class:`Filter`: A Filter class which inherits from :class:`BaseFilter`
        """
        pattern = Instagram.link_pattern

        class Filter(BaseFilter):
            def filter(self, message):
                return bool(pattern.findall(message.text))

        return Filter()

    @run_async
    def insta(self, bot: Bot, update: Update, args: list = None):
        """Download a post

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of arguments passed by the user. First argument must be must be a link
                to a post or the posts id
        """
        if len(args) != 1:
            update.message.reply_text('You have to give me the link or the post id.')
            return

        post_token = self.link_to_post_token(args[0]) or args[0]
        telegram_user = None
        is_public = True
        if not self.is_post_public(post_token):
            is_public = False
            telegram_user = update.message.from_user.username

            if not self.logged_in(telegram_user):
                update.message.reply_text('This content is private, please login first.')
                return

        looter = self.get_looter(telegram_username=telegram_user)
        if not looter:
            update.message.reply_text(
                'There was a problem while logging in, please logout (/instalo) and login (/instali)again.')
            return
        post = looter.get_post_info(post_token)

        try:
            chat_id = update.message.chat_id
            if is_public:
                media_array = self.get_linked_input_media_from_post(post)
            else:
                media_array = self.get_file_input_media_from_post(update, looter, post)

            if len(media_array) > 1:
                bot.send_media_group(chat_id, media_array, reply_to_message_id=update.message.message_id)
            elif post['is_video']:
                bot.send_video(chat_id, media_array[0].media)
            else:
                bot.send_photo(chat_id, media_array[0].media)
        except KeyError:
            update.message.reply_text(
                'Could not get image, either the provided post link / id is incorrect or the user is private.')

    @run_async
    def instap(self, bot: Bot, update: Update, args: list = None):
        """Download all posts from a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of arguments passed by the user. First argument must be must be a link to
                a user or his username
        """
        if len(args) != 1:
            update.message.reply_text('You have to give me the link or the username.')
            return

        username = self.link_to_username(args[0]) or args[0]
        telegram_user = None

        is_public = True
        if not self.is_public_profile(username):
            is_public = False
            telegram_user = update.message.from_user.username

            if not self.logged_in(telegram_user):
                update.message.reply_text('This content is private, please login first.')
                return

        looter = self.get_looter(telegram_username=telegram_user, profile=username)
        if not looter:
            update.message.reply_text(
                'There was a problem while logging in, please logout (/instalo) and login (/instali)again.')
            return

        media_generator = looter.medias(with_pbar=True)
        try:
            chat_id = update.message.chat_id

            def send_media_array(medias):
                bot.send_chat_action(chat_id, ChatAction.UPLOAD_PHOTO)
                if 1 < len(medias):
                    bot.send_media_group(chat_id, medias, disable_notification=True)
                elif isinstance(medias[0], InputMediaVideo):
                    bot.send_video(chat_id, medias, disable_notification=True)
                else:
                    bot.send_photo(chat_id, medias, disable_notification=True)

            media_array = []
            for media in media_generator:
                post = looter.get_post_info(media['code'])
                if is_public:
                    media_array += self.get_linked_input_media_from_post(post)
                else:
                    media_array += self.get_file_input_media_from_post(update, looter, post)
                if len(media_array) >= 10:
                    send_media_array(media_array[:10])
                    del media_array[:10]
            if media_array:
                send_media_array(media_array)
        except KeyError:
            update.message.reply_text(
                'Could not get image, either the provided post link / id is incorrect or the user is private.')
        update.message.reply_text('Everything has been sent.')

    def instali(self, bot: Bot, update: Update, args: list = None):
        """Login the user to instagram

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of arguments passed by the user. First argument must be must be the
                username and the second the password
        """
        telegram_user = update.message.from_user.username
        if self.logged_in(telegram_user):
            update.message.reply_text('Already logged in as %s' % self.current_user(telegram_user)['username'])
        else:
            if len(args) < 2 or len(args) > 2:
                update.message.reply_text('You have to give me the username and password.')
                return
            username, password = args
            insta_looter = InstaLooter()
            try:
                insta_looter.login(username, password)
                self.safe_login(telegram_user, username, password)
                update.message.reply_text('Logged in')
            except ValueError:
                update.message.reply_text('Username or password wrong')

    def instalo(self, bot: Bot, update: Update):
        """Logout the instagram user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        if self.logged_in(update.message.from_user.username):
            if self.remove_user(update.message.from_user.username):
                update.message.reply_text('Logged out')
        else:
            update.message.reply_text('You were not logged in')

    def insta_link_auto(self, bot: Bot, update: Update):
        """Auto read instagram urls

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        post_token = self.link_to_post_token(update.message.text)
        if post_token:
            self.insta(bot, update, [post_token, ])

    def get_file_input_media_from_post(self, update: Update, looter: InstaLooter, post: dict) -> list:
        """Download a post by its link

        Args:
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            looter (:class:`InstaLooter`): A logged in InstaLooter object
            post (:obj:`dict`): The post object given by InstaLooter

        Returns:
            :obj:`list`: List of input media classes :class:`InputMediaPhoto` and :class:`InputMediaVideo`
        """
        result = []
        with self.download_to_object(looter, post) as files:
            if not files:
                update.message.reply_text('Something went wrong while downloading the post, please try again')

            if post['is_video']:
                result.append(InputMediaVideo(media=open(files[0], 'rb')))
            else:
                for file in files:
                    result.append(InputMediaPhoto(media=open(file, 'rb')))
        return result

    def get_linked_input_media_from_post(self, post: dict) -> list:
        """Send post as link to telegram

        Args:
            post (:obj:`dict`): The post object given by InstaLooter

        Returns:
            :obj:`list`: List of input media classes :class:`InputMediaPhoto` and :class:`InputMediaVideo`
        """
        result = []
        if post['is_video']:
            result.append(InputMediaVideo(media=post['video_url']))
        else:
            if post.get('edge_sidecar_to_children', None):
                for photo in post['edge_sidecar_to_children']['edges']:
                    result.append(InputMediaPhoto(media=photo['node']['display_url']))
            else:
                result.append(InputMediaPhoto(media=post['display_src']))
        return result

    def logged_in(self, telegram_username: str) -> bool:
        """Check if user is logged into Instagram

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.

        Returns:
            :obj:`bool`: Returns whether the user is logged in ot not
        """
        return bool(self.current_user(telegram_username))

    def current_user(self, telegram_username: str) -> str:
        """Get Instagram username of Telegram user

        Args:
            telegram_username (:obj:`str`): Username of the Telegram user.

        Returns:
            :obj:`str`: Returns the name if existing otherwise None
        """
        user_dict = data.get(self.data_name)
        return user_dict.get(telegram_username, None)

    def remove_user(self, telegram_username: str) -> bool:
        """Remove login of a specific Telegram user

        Args:
            telegram_username (:obj:`str`): Username of the Telegram user.

        Returns:
            :obj:`bool`: Returns true if the user was removed and false if the user didn't exist
        """
        user_dict = data.get(self.data_name)
        if user_dict.get(telegram_username, None):
            del user_dict[telegram_username]
            data.save(self.data_name, user_dict)
            return True
        return False

    def safe_login(self, telegram_username: str, username: str, password: str) -> bool:
        """Safe the login for a user

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.
            username (:obj:`str`): Username of the instagram user.
            password (:obj:`str`): Password of the instagram user.

        Returns:
            :obj:`bool`: Returns true if the user was removed and false if the user didn't exist
        """
        user_dict = data.get(self.data_name)
        data.save(self.data_name, {
            **user_dict,
            **{
                telegram_username: {
                    'username': username,
                    'password': password
                }
            }
        })

    def get_looter(self, telegram_username: str = None, profile: str = None) -> InstaLooter:
        """Create a :class:`InstaLooter` instance

        Args:
            telegram_username (:obj:`str`, optional): Username of the Telegram user to directly log in.
            profile (:obj:`str`, optional): Username of an Instagram user.

        Returns:
            :class:`InstaLooter`: An InstaLooter object
        """
        insta_looter = InstaLooter(profile=profile)

        if telegram_username:
            user = self.current_user(telegram_username)
            try:
                insta_looter.login(**user)
            except ValueError:
                return False

        return insta_looter

    @contextmanager
    def download_to_object(self, looter: InstaLooter, media: dict) -> list:
        """Download a post

        Args:
            looter (:obj:`looter`): A InstaLooter object
            media (:obj:`dict`): A post dictionary given by the instagram api

        Returns:
            :obj:`list`: List of files downloaded (it is possible for one post to have multiple images)
        """
        post_code = media['code']

        with TemporaryDirectory() as temp_dir:
            looter.directory = temp_dir
            looter.download_post(post_code)

            yield [os.path.join(temp_dir, file_path) for file_path in os.listdir(temp_dir)]

    def link_to_post_token(self, post_link: str) -> str:
        """Converts a post link to its token

        Args:
            post_link (:obj:`str`): The link to a post

        Returns:
            :obj:`str`: Post token
        """
        post_pattern = re.compile(self.link_pattern.pattern + '/p/')
        if post_pattern.findall(post_link):
            path = post_pattern.sub('', post_link)
            post_token = path.split('?', 1)[0].strip(' /')
            return post_token

    def link_to_username(self, user_link: str) -> str:
        """Converts a user link to its username

        Args:
            user_link (:obj:`str`): The link to a user

        Returns:
            :obj:`str`: The users username
        """
        if self.link_pattern.findall(user_link):
            path = self.link_pattern.sub('', user_link)
            username = path.split('?', 1)[0].strip(' /')
            return username

    def is_post_public(self, post: str) -> bool:
        """Check if the post is public or not

        Args:
            post (:obj:`str`): Either the link to a post or the post_id

        Returns:
            :obj:`bool`: True if it is public false if not
        """
        if not self.link_pattern.findall(post):
            post = 'https://{}/p/{}'.format(self.base_url, post)
        request = requests.head(post)
        return 200 <= request.status_code < 400

    def is_public_profile(self, user: str) -> bool:
        """Check if the profile is pubic

        Args:
            user (:obj:`str`): Either the link to a user or the username

        Returns:
            :obj:`bool`: True if it is public false if not
        """
        if not self.link_pattern.findall(user):
            user = 'https://{}/{}'.format(self.base_url, user)
        request = requests.get(user)

        return b'"is_private": true' not in request.content


instagram = Instagram()
