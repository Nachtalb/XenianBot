import os
import re
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from instaLooter import InstaLooter
from telegram import Bot, ChatAction, MessageEntity, Update
from telegram.ext import Filters, MessageHandler, run_async

from xenian_bot.commands import BaseCommand
from xenian_bot.utils import data

__all__ = ['instagram_post_download', 'instagram_profil_download', 'instagram_login', 'instagram_logout',
           'auto_instargam_downloader']


class InstagramMixims:
    data_name = 'instagram'
    base_url = 'instagram.com'

    def download_n_send_post(self, bot: Bot, update: Update, looter: InstaLooter, post: dict):
        """Download a post by its link

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            looter (:class:`InstaLooter`): A logged in InstaLooter object
            post (:obj:`dict`): The post object given by InstaLooter

        Returns:
            :obj:`object`: File like object of the image
        """
        with self.download_to_object(looter, post) as files:
            if not files:
                update.message.reply_text('Something went wrong while downloading the post, please try again')

            if post['is_video']:
                bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_VIDEO)
                bot.send_video(update.message.chat_id, video=open(files[0], 'rb'))
            else:
                for file in files:
                    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.UPLOAD_PHOTO)
                    bot.send_photo(update.message.chat_id, photo=open(file, 'rb'))

    def logged_in(self, telegram_username: str):
        """Check if user is logged into instagram

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.

        Returns:
            (:obj:`bool`): Returns whether the user is logged in ot not
        """
        return bool(self.current_user(telegram_username))

    def current_user(self, telegram_username: str):
        """Get instagram username of telegram user

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.

        Returns:
            (:obj:`str` or :obj:`None`): Returns the name if existing otherwise None
        """
        user_dict = data.get(self.data_name)
        return user_dict.get(telegram_username, None)

    def remove_user(self, telegram_username: str):
        """Remove login of a specific telegram user

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.

        Returns:
            (:obj:`bool`): Returns true if the user was removed and false if the user didn't exist
        """
        user_dict = data.get(self.data_name)
        if user_dict.get(telegram_username, None):
            del user_dict[telegram_username]
            data.save(self.data_name, user_dict)
            return True
        return False

    def safe_login(self, telegram_username: str, username: str, password: str):
        """Safe the login for a user

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.
            username (:obj:`str`): Username of the instagram user.
            password (:obj:`str`): Password of the instagram user.

        Returns:
            (:obj:`bool`): Returns true if the user was removed and false if the user didn't exist
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

    def get_logged_in_looter(self, telegram_username: str, profile: str = None):
        """Safe the login for a user

        Args:
            telegram_username (:obj:`str`): Username of the telegram user.
            profile (:obj:`str`): Username of an instagram user.

        Returns:
            (:class:`InstaLooter`): An InstaLooter object with a logged in user
        """
        user = self.current_user(telegram_username)
        insta_looter = InstaLooter(profile=profile)
        try:
            insta_looter.login(**user)
            return insta_looter
        except ValueError:
            return False

    @contextmanager
    def download_to_object(self, looter: InstaLooter, media: dict):
        """Download a post

        Args:
            looter (:obj:`looter`): A InstaLooter object
            media (:obj:`dict`): A post dictionary given by the instagram api

        Returns:
            List of files downloaded (it is possible for one post to have multiple images)
        """
        post_code = media['code']

        with TemporaryDirectory() as temp_dir:
            looter.directory = temp_dir
            looter.download_post(post_code)

            yield [os.path.join(temp_dir, file_path) for file_path in os.listdir(temp_dir)]


class InstagramPostDownload(InstagramMixims, BaseCommand):
    command_name = 'insta'
    title = 'Instagram Post Download'
    description = 'Download a post from Instagram via its link or its ID'
    args = 'POST_LINK OR POST_ID'

    def __init__(self):
        super(InstagramPostDownload, self).__init__()
        self.options['pass_args'] = True

    @run_async
    def command(self, bot: Bot, update: Update, args: list = None, quiet=False):
        """Download a post

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of arguments passed by the user. First argument must be must be a link to a post or
                the posts id
            quiet (:obj:`bool`): If errors should be sent to the user
        """
        if len(args) != 1:
            if not quiet:
                update.message.reply_text('You have to give me the link or the post id.')
            return

        telegram_user = update.message.from_user.username
        if not self.logged_in(telegram_user):
            if not quiet:
                update.message.reply_text('You first have to login /instali.')
            return

        post_token = args[0].strip()
        if '/' in post_token:
            http_re = re.compile('^((http(s)?:)?//)?(www\.)?')
            sent = http_re.sub('', post_token)
            path = sent.replace(self.base_url, '')
            post_token = path.replace('/p/', '').split('?', 1)[0].strip(' /')

        try:
            looter = self.get_logged_in_looter(telegram_user)
            if not looter:
                if not quiet:
                    update.message.reply_text(
                        'There was a problem while logging in, please logout (/instalo) and login (/instali)again.')
                return
            post = looter.get_post_info(post_token)
            self.download_n_send_post(bot, update, looter, post)
        except KeyError:
            if not quiet:
                update.message.reply_text(
                    'Could not get image, either the provided post link / id is incorrect or the user is private.')


instagram_post_download = InstagramPostDownload()


class InstagramProfileDownload(InstagramMixims, BaseCommand):
    command_name = 'instap'
    title = 'Instagram Profile Download'
    description = 'Download a all posts from an user'
    args = 'POST_LINK OR USERNAME'

    def __init__(self):
        super(InstagramProfileDownload, self).__init__()
        self.options['pass_args'] = True

    @run_async
    def command(self, bot: Bot, update: Update, args: list = None):
        """Download all posts from a user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of arguments passed by the user. First argument must be must be a link to a user or
                his username
        """
        if len(args) != 1:
            update.message.reply_text('You have to give me the link or the username.')
            return

        telegram_user = update.message.from_user.username
        if not self.logged_in(telegram_user):
            update.message.reply_text('You first have to login /instali.')
            return

        username = args[0].strip()
        if '/' in username:
            http_re = re.compile('^((http(s)?:)?//)?(www\.)?')
            sent = http_re.sub('', username)
            path = sent.replace(self.base_url, '')
            username = path.split('?', 1)[0].strip(' /')

        try:
            looter = self.get_logged_in_looter(telegram_user, username)
            if not looter:
                update.message.reply_text(
                    'There was a problem while logging in, please logout (/instalo) and login (/instali)again.')
                return

            media_generator = looter.medias(with_pbar=True)
            for media in media_generator:
                self.download_n_send_post(bot, update, looter, media)
        except KeyError:
            update.message.reply_text(
                'Could not get image, either the provided post link / id is incorrect or the user is private.')


instagram_profil_download = InstagramProfileDownload()


class InstagramLogin(InstagramMixims, BaseCommand):
    command_name = 'instali'
    title = 'Instagram Login'
    description = 'Login to instagram. DO NOT USE THIS IN GROUPS you can login in privat chat with @XenianBot'
    args = 'USERNAME PASSWORD'

    def __init__(self):
        super(InstagramLogin, self).__init__()
        self.options['pass_args'] = True

    def command(self, bot: Bot, update: Update, args: list = None):
        """Login the user to instagram

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`): List of arguments passed by the user. First argument must be must be the username and
                the second the password
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


instagram_login = InstagramLogin()


class InstagramLogout(InstagramMixims, BaseCommand):
    command_name = 'instalo'
    title = 'Instagram Logout'
    description = 'Logout from instagram'

    def command(self, bot: Bot, update: Update):
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


instagram_logout = InstagramLogout()


class AutoInstargamDownloader(InstagramMixims, BaseCommand):
    hidden = True
    handler = MessageHandler

    def __init__(self):
        super(AutoInstargamDownloader, self).__init__()
        self.options = {
            'callback': self.command,
            'filters': Filters.entity(MessageEntity.URL)
        }

    def command(self, bot: Bot, update: Update):
        """Auto read instagram urls

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        telegram_user = update.message.from_user.username
        if self.logged_in(telegram_user):
            text = update.message.text
            http_re = re.compile('^((http(s)?:)?//)?(www\.)?')
            sent = http_re.sub('', text)
            path = sent.replace(self.base_url, '')

            if path.startswith('/p/'):
                post_token = path.replace('/p/', '').split('?', 1)[0].strip(' /')
                instagram_post_download.command(bot, update, [post_token], quiet=True)


auto_instargam_downloader = AutoInstargamDownloader()
