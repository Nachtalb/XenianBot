import logging
import os
import re
from contextlib import contextmanager
from tempfile import TemporaryDirectory

import instabot
import logzero
from instaLooter import InstaLooter
from telegram import Bot, ChatAction, InputMediaPhoto, InputMediaVideo, MessageEntity, Update
from telegram.ext import BaseFilter, Filters, MessageHandler, run_async

from xenian_bot.commands.filters.download_mode import download_mode_filter
from xenian_bot.settings import INSTAGRAM_CREDENTIALS, LOG_LEVEL
from . import BaseCommand

__all__ = ['instagram']

logger = logzero.setup_logger(name=__name__, level=LOG_LEVEL)


class Instagram(BaseCommand):
    """Instagram Downloader integration for this bot


    Attributes:
        data_name (:obj:`str`): The name for the data set where the user credentials are saved
        base_url (:obj:`str`): Base URL of Instagram
        link_pattern (:obj:`_sre.SRE_Pattern`): A regex compiled string which matches any Instagram link
        looter (:obj:`InstaLooter`): Logged in looter for Instagram
        bot_api (:obj:`instabot.Bot`): Instagram bot used to follow people
        logged_in (:obj:`bool`): If login at start of bot was successful
    """
    data_name = 'instagram'
    base_url = 'instagram.com'
    link_pattern = re.compile('^((http(s)?:)?//)?(www\.)?{}'.format(base_url.replace('.', '\.')))
    looter = InstaLooter()
    bot_api = instabot.Bot(
        max_followers_to_follow=64**64,  # take any really big number
        max_following_to_follow=64**64,
        max_followers_to_following_ratio=64**64,
        max_following_to_followers_ratio=64**64,
    )
    logged_in = False

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
                'title': 'Instagram Follow',
                'description': 'Tell @XenianBot to follow a specific user on Instagram, this is used to access private '
                               'accounts.',
                'args': 'PROFILE_LINK/S OR USERNAME/S',
                'command': self.insta_follow,
                'options': {'pass_args': True}
            },
            {
                'title': 'Instagram Auto Link',
                'description': 'Turn on /download_mode and send links to Instagram posts to auto-download them',
                'command': self.insta_link_auto,
                'handler': MessageHandler,
                'options': {
                    'filters': Filters.entity(MessageEntity.URL) & download_mode_filter & Instagram.insta_link_filter()
                },
            }
        ]
        self.login()

        super(Instagram, self).__init__()

    def login(self):
        if not self.logged_in and 'username' in INSTAGRAM_CREDENTIALS and 'password' in INSTAGRAM_CREDENTIALS:
            try:
                logging.info('Login to InstaLooter')
                self.looter.login(**INSTAGRAM_CREDENTIALS)
                logging.info('Login to InstaBot')
                self.bot_api.login(**INSTAGRAM_CREDENTIALS)
                self.logged_in = True
            except ValueError:
                pass

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
        try:
            post = self.looter.get_post_info(post_token)
        except KeyError:
            update.message.reply_text('This content is non existing or private, please use `/insta_follow USERNAME` '
                                      'so I can follow the account.')
            return

        try:
            chat_id = update.message.chat_id
            media_array = self.get_file_input_media_from_post(update, post)

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

        self.looter.target = username
        if not self.is_public_profile(username):
            self.bot_api.follow(username)
            update.message.reply_text('The account you sent me is private. I started following the account please try '
                                      'later again to see if the follow request was accepted')
            return

        media_generator = self.looter.medias(with_pbar=True)
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
                post = self.looter.get_post_info(media['code'])
                media_array += self.get_file_input_media_from_post(update, post)

                if len(media_array) >= 10:
                    send_media_array(media_array[:10])
                    del media_array[:10]
            if media_array:
                send_media_array(media_array)
        except KeyError:
            update.message.reply_text(
                'Could not get image, either the provided post link / id is incorrect or the user is private.')
        update.message.reply_text('Everything has been sent.')

    @run_async
    def insta_follow(self, bot: Bot, update: Update, args: list = None):
        """Follow a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of arguments passed by the user. First argument must be must be a link to
                a user or his username
        """
        if not args:
            update.message.reply_text('You have to give me at lease one link or one username.')
            return

        user_names = []
        for user in args:
            user_names.append(self.link_to_username(user))

        self.bot_api.follow_users(args)
        update.message.reply_text('I started following these users: {}'.format(', '.join(user_names)))

    def insta_link_auto(self, bot: Bot, update: Update):
        """Auto read instagram urls

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        post_token = self.link_to_post_token(update.message.text)
        if post_token:
            self.insta(bot, update, [post_token, ])

    def get_file_input_media_from_post(self, update: Update, post: dict) -> list:
        """Download a post by its link

        Args:
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            post (:obj:`dict`): The post object given by InstaLooter

        Returns:
            :obj:`list`: List of input media classes :class:`InputMediaPhoto` and :class:`InputMediaVideo`
        """
        result = []
        with self.download_to_object(self.looter, post) as files:
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
        return post_link

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
        return user_link

    def is_public_profile(self, user: str) -> bool:
        """Check if the profile is pubic

        Args:
            user (:obj:`str`): Either the link to a user or the username

        Returns:
            :obj:`bool`: True if it is public false if not
        """
        username = self.link_to_username(user)
        user_info = self.bot_api.get_user_info(username)
        return user_info['is_private']


instagram = Instagram()
