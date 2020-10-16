import os
import re
import shutil

from PIL import Image
from io import BufferedWriter
from tempfile import NamedTemporaryFile, TemporaryDirectory
from uuid import uuid4

import youtube_dl
from moviepy.video.io.VideoFileClip import VideoFileClip
from telegram import Bot, ChatAction, Document, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, ParseMode, \
    Sticker, Update, Video
from telegram.error import BadRequest, NetworkError, TimedOut
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler, run_async
from youtube_dl import DownloadError

from xenian.bot.settings import UPLOADER
from xenian.bot.uploaders import uploader
from xenian.bot.utils import CustomNamedTemporaryFile, TelegramProgressBar, save_file
from . import BaseCommand
from .filters.download_mode import download_mode_filter

__all__ = ['download', 'video_downloader']


class Download(BaseCommand):
    group = 'Download'
    ram_db = {}

    def __init__(self):
        self.commands = [
            {
                'title': 'Toggle Download Mode on / off',
                'description': 'If on download stickers and gifs sent to the bot of off reverse search is reactivated. '
                               'Does not work in groups',
                'command_name': 'download_mode',
                'command': self.toggle_download_mode,
                'options': {'filters': ~ Filters.group}
            },
            {
                'title': 'Toggle Zip Download Mode on / off',
                'description': 'If zip mode is on collect all downloads and zip them upon disabling zip mode',
                'command_name': 'zip_mode',
                'command': self.toggle_zip_mode,
                'options': {'filters': ~ Filters.group}
            },
            {
                'title': 'Clear ZIP download queue',
                'description': 'Clear ZIP download queue',
                'command': self.zip_clear,
                'options': {'filters': ~ Filters.group}
            },
            {
                'title': 'Download Stickers',
                'description': 'Turn on /download_mode and send stickers',
                'handler': MessageHandler,
                'command': self.download_stickers,
                'options': {'filters': Filters.sticker & download_mode_filter & ~ Filters.group}
            },
            {
                'title': 'Download Gifs',
                'description': 'Turn on /download_mode and send videos and gifs',
                'handler': MessageHandler,
                'command': self.download_gif,
                'options': {'filters': (Filters.video | Filters.document) & download_mode_filter & ~ Filters.group}
            },
            {
                'description': 'Reply to media for download',
                'command': self.download,
            }
        ]

        super(Download, self).__init__()

    def toggle_download_mode(self, bot: Bot, update: Update):
        """Toggle Download Mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        mode_on = download_mode_filter.toggle_mode(update.message.from_user.id)
        if mode_on:
            update.message.reply_text('Download Mode on')
        else:
            update.message.reply_text('Download Mode off')

    def toggle_zip_mode(self, bot: Bot, update: Update):
        """Toggle Zip Mode

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        mode_on = download_mode_filter.toggle_mode(update.message.from_user.id, zip_mode=True)
        if mode_on:
            in_queue = len(self.ram_db.get(update.message.from_user.id, []))
            append = (f'\nThere are still `{in_queue}` Items in the Download queue. Use /zip\_clear to clear the queue.'
                if in_queue else '')
            update.message.reply_text(f'Download Zip Mode on{append}', parse_mode=ParseMode.MARKDOWN)
        else:
            self.download_zip(bot, update, update.message.from_user.id)
            update.message.reply_text('Download Mode off')

    def zip_clear(self, bot: Bot, update: Update):
        """Clear ZIP download queue

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        self.ram_db[update.message.from_user.id] = []
        update.message.reply_text('ZIP download queue was cleared.', reply_to_message_id=update.message.message_id)

    def add_to_zip(self, update, user_id, item):
        update.message.reply_text('Item was added', reply_to_message_id=update.message.message_id)
        self.ram_db.setdefault(user_id, [])
        self.ram_db[user_id].append(item)

    @run_async
    def download_zip(self, bot, update, user_id):
        """Send Zip with all given files to user

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            user_id (:obj:`int`): Id of a user
        """
        message = update.message
        user_files = self.ram_db.get(user_id)
        if not user_files:
            update.message.reply_text('No files sent for download')
            return

        with TemporaryDirectory() as temp_folder:
            zip_content_path = os.path.join(temp_folder, 'zip_content')
            os.mkdir(zip_content_path)

            progress_bar = TelegramProgressBar(
                bot=bot,
                chat_id=update.message.chat_id,
                full_amount=len(user_files),
                pre_message='Downloading files\n{current} / {total}',
                se_message='Downloading GIFs may take a while.'
            )
            progress_bar.start()

            for index, file in enumerate(user_files):
                temp_file = None
                if isinstance(file, Sticker):
                    temp_file = NamedTemporaryFile(delete=False, dir=zip_content_path, prefix='xenian-', suffix='.png')
                    self.download_stickers_to_file(bot, file, temp_file)

                elif isinstance(file, Document) or isinstance(file, Video):
                    temp_file = NamedTemporaryFile(delete=False, dir=zip_content_path, prefix='xenian-', suffix='.gif')
                    _, orig_path, compressed_path = self.download_video_to_file(bot, file, temp_file, temp_file.name)

                if temp_file:
                    temp_file.close()
                progress_bar.update(new_amount=index + 1)

            zip_path = os.path.join(temp_folder, os.path.basename(f'downloads_{user_id}'))
            os.chmod(zip_content_path, 0o40755)
            created_zip = shutil.make_archive(zip_path, format='zip', root_dir=zip_content_path, base_dir='.')

            if os.path.getsize(created_zip) > 52428800:
                message.reply_text('File is too big, sorry!', reply_to_message_id=message.message_id)
            else:
                with open(created_zip, mode='br') as zip_file:
                    message.reply_document(zip_file, filename=os.path.basename(created_zip), timeout=50,
                                           reply_to_message_id=message.message_id)

    def download_stickers_to_file(self, bot: Bot, sticker: Sticker, file_object: BufferedWriter):
        """Download Sticker as images to file_object

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            sticker (:obj:`telegram.sticker.Sticker`): A Sticker object
            file_object (:obj:`io.BufferedWriter`): File like object
        """
        sticker = bot.get_file(sticker.file_id)
        sticker.download(out=file_object)

        if getattr(file_object, 'save', None):
            file_object.save()
        else:
            save_file(file_object)

        image = Image.open(file_object.name)
        image.save(file_object, format='png')

        return file_object

    @run_async
    def download_stickers(self, bot: Bot, update: Update):
        """Download Sticker as images

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        orig_sticker = update.message.sticker or update.message.reply_to_message.sticker

        user_id = update.message.from_user.id
        if download_mode_filter.is_zip_mode_on(user_id):
            self.add_to_zip(update, user_id, orig_sticker)
            return

        with CustomNamedTemporaryFile(suffix='.png', prefix='xenian-') as image:
            self.download_stickers_to_file(bot, orig_sticker, image)
            image.seek(0)
            bot.send_photo(update.message.chat_id, photo=image)

    def download_video_to_file(self, bot: Bot, document: Document, file_object: BufferedWriter, file_object_path: str):
        """Download Sticker as images to file_object

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            document (:obj:`telegram.document.Document`): A Telegram API Document object
            file_object (:obj:`io.BufferedWriter`): Actual existing file object
            file_object_path (:obj:`str`): The path to the file given in file_object
        """
        video = bot.getFile(document.file_id)

        with CustomNamedTemporaryFile() as video_file:
            video.download(out=video_file)
            video_file.close()
            video_clip = VideoFileClip(video_file.name, audio=False)

            video_clip.write_gif(file_object_path)
            video_clip.close()

            dirname = os.path.dirname(file_object_path)
            file_name = os.path.splitext(file_object_path)[0]
            compressed_gif_path = os.path.join(dirname, file_name + '-min.gif')

            os.system('gifsicle -O3 --lossy=50 -o {dst} {src}'.format(dst=compressed_gif_path, src=file_object_path))
            compressed_gif_path = compressed_gif_path if os.path.isfile(compressed_gif_path) else ''
            return file_object, file_object_path, compressed_gif_path

    @run_async
    def download_gif(self, bot: Bot, update: Update):
        """Download videos as gifs

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        message = update.message
        bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)

        document = (update.message.document or update.message.video or update.message.reply_to_message.document or
                    update.message.reply_to_message.video)

        user_id = update.message.from_user.id
        if download_mode_filter.is_zip_mode_on(user_id):
            self.add_to_zip(update, user_id, document)
            return

        with CustomNamedTemporaryFile(suffix='.gif') as video_file:
            _, orig_path, compressed_path = self.download_video_to_file(bot, document, video_file, video_file.name)

            uploader.connect()
            upload_path = UPLOADER.get('url', None) or UPLOADER['configuration'].get('path', None) or ''

            upload_orig_file_name = 'xenian-{}.gif'.format(str(uuid4())[:8])
            uploader.upload(orig_path, upload_orig_file_name)

            orig_host_path = upload_path + '/' + upload_orig_file_name

            compressed_host_path = None
            if os.path.isfile(compressed_path):
                upload_compressed_file_name = 'xenian-{}-min.gif'.format(str(uuid4())[:8])
                uploader.upload(compressed_path, upload_compressed_file_name)
                compressed_host_path = upload_path + '/' + upload_compressed_file_name

            # If the host path a local path we can't send it as an URL, so we send the gif just as a ZIP file.
            if os.path.isfile(orig_host_path):
                with TemporaryDirectory() as temp_folder:
                    zip_content_path = os.path.join(temp_folder, 'zip_content')
                    os.mkdir(zip_content_path)
                    uploader.upload(orig_host_path, zip_content_path)
                    if compressed_host_path:
                        uploader.upload(compressed_host_path, zip_content_path)

                    zip_path = os.path.join(temp_folder, os.path.basename(orig_host_path))
                    os.chmod(zip_content_path, 0o40755)
                    created_zip = shutil.make_archive(zip_path, format='zip', root_dir=zip_content_path, base_dir='.')
                    if os.path.getsize(created_zip) > 52428800:
                        message.reply_text('File is too big, sorry!', reply_to_message_id=message.message_id)
                    else:
                        with open(created_zip, mode='br') as zip_file:
                            message.reply_document(zip_file, filename=os.path.basename(created_zip),
                                                   reply_to_message_id=message.message_id)
                uploader.close()
                return
            uploader.close()

            downloadable_file = compressed_host_path or orig_host_path

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Download GIF", url=downloadable_file), ], ])
            message.reply_photo(downloadable_file, 'Instant GIF Download', reply_markup=reply_markup,
                                reply_to_message_id=message.message_id)

    @run_async
    def download(self, bot: Bot, update: Update):
        """Reply to media to reverse search

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        reply_to_message = update.message.reply_to_message
        if not reply_to_message:
            update.message.reply_text('You have to reply to some media file to start the download.')
        if reply_to_message.sticker:
            self.download_stickers(bot, update)
        if reply_to_message.video or reply_to_message.document:
            self.download_gif(bot, update)


download = Download()


class VideoDownloader(BaseCommand):
    keyboard_message_id = {}
    """Keyboard message chat id of current download

    Key must always be user_id

    Examples:
        keyboard_message_id = {
            'some_user': 'message_id'
        }
    """

    current_menu = {}
    """Which menu the user is in

    Key must always be user_id
    Possible menus: 'format', 'audio', 'video', 'video_quality', 'audio_quality'

    Examples:
        current_menu = {
            'some_user': 'video'
        }
    """

    video_information = {}
    """Extracted video information

    Key must always be user_id
    """

    group = 'Download'

    def __init__(self):
        self.commands = [
            {
                'title': 'Video from URL',
                'description': 'Turn on /download_mode and send links to videos like a youtube video',
                'handler': MessageHandler,
                'command': self.video_from_url,
                'options': {'filters': Filters.entity(MessageEntity.URL) & download_mode_filter & ~ Filters.group}
            },
            {
                'description': 'Video Download Menu Changes',
                'command': self.menu_change,
                'handler': CallbackQueryHandler,
                'options': {'pattern': '^(video|audio|format)'},
                'hidden': True
            },
            {
                'description': 'Abort Video Download',
                'command': self.abort,
                'handler': CallbackQueryHandler,
                'options': {'pattern': '^abort$'},
                'hidden': True
            },
            {
                'description': 'Download the video / audio',
                'command': self.download,
                'handler': CallbackQueryHandler,
                'options': {'pattern': '^download'},
                'hidden': True
            }
        ]
        super(VideoDownloader, self).__init__()

    @run_async
    def video_from_url(self, bot: Bot, update: Update):
        """Download video from URL

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        user_id = update.message.from_user.id

        if self.video_information.get(user_id, None):
            self.abort(bot, update)

        chat_id = update.message.chat_id
        url = update.message.text
        url = re.sub('&list.*$', '', url)

        with youtube_dl.YoutubeDL({}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except DownloadError:
                return
            info['short_description'] = re.sub(r'\n\s*\n', '\n', info.get('description', ''))
            self.video_information[user_id] = info
            keyboard = self.get_keyboard('format', info)

            self.current_menu[user_id] = 'format'
            self.keyboard_message_id[user_id] = bot.send_message(
                chat_id=chat_id,
                text='<a href="{webpage_url}">&#8205;</a>'
                     '{extractor_key:-^20}\n'
                     '<b>{title}</b>\n'
                     '{short_description:.150}...\n'
                     '- {uploader}\n'.format(**info),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
                reply_markup=keyboard
            )

    @run_async
    def download(self, bot: Bot, update: Update):
        """Download video from URL

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        url = self.video_information[user_id]['webpage_url']
        data = update.callback_query.data.split(' ')

        class DownloadHook:
            progress_bar = None
            can_send_status = True

            def hook(self, download_event: dict):
                """Hook for download

                Args:
                    download_event (:obj:`dict`): Dictionary with information about the event and the file
                """
                if download_event['status'] == 'downloading' and self.can_send_status:
                    total_amount = download_event.get('total_bytes', None)
                    downloaded = download_event['downloaded_bytes']
                    fragments = False

                    if not total_amount:
                        fragments = True
                        total_amount = download_event.get('fragment_count', None)
                        downloaded = download_event.get('fragment_index', None)

                    if total_amount is not None:
                        if self.progress_bar is None:
                            self.progress_bar = TelegramProgressBar(
                                bot=bot,
                                chat_id=chat_id,
                                full_amount=total_amount if fragments else total_amount / 1000000,
                                pre_message='Downloading Video\n{current} / {total} %s' % (
                                    'fragments' if fragments else 'MB')
                            )
                            self.progress_bar.start()
                            return
                        self.progress_bar.update(
                            new_amount=downloaded if fragments else downloaded / 1000000,
                            new_full_amount=total_amount if fragments else total_amount / 1000000
                        )
                    else:
                        self.can_send_status = False
                        bot.send_message(chat_id=chat_id, text='Downloading Video\nNo download status available.')

        format_id = data[2]
        if format_id == 'best':
            if data[1] == 'video':
                format_id = 'bestvideo/best'
            elif data[1] == 'audio':
                format_id = 'bestaudio'
            elif data[1] == 'video_audio':
                format_id = 'best'

        with TemporaryDirectory() as temp_dir:
            download_hook = DownloadHook()
            options = {
                'format': format_id,
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'restrictfilenames': True,
                'progress_hooks': [download_hook.hook],
            }

            if data[1] == 'audio' and data[2] == 'best':
                options['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

            with youtube_dl.YoutubeDL(options) as ydl:
                bot.edit_message_reply_markup(
                    chat_id=update.effective_chat.id,
                    message_id=self.keyboard_message_id[user_id].message_id,
                    reply_markup=[])

                ydl.download([url, ])

                filename = os.listdir(temp_dir)[0]
                file_path = os.path.join(temp_dir, filename)

                file_size = os.path.getsize(file_path)
                sent = False
                if file_size < 5e+7:
                    try:
                        bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

                        bot.send_message(chat_id=chat_id, text='Depending on the filesize the upload could take some '
                                                               'time')
                        bot.send_document(chat_id=chat_id, document=open(file_path, mode='rb'), filename=filename,
                                          timeout=60)
                        sent = True
                    except (NetworkError, TimedOut, BadRequest):
                        pass

                if not sent:
                    bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
                    uploader.connect()
                    uploader.upload(file_path, remove_after=1800)
                    uploader.close()

                    path = UPLOADER.get('url', None) or UPLOADER['configuration'].get('path', None) or ''
                    url_path = os.path.join(path, filename)

                    if os.path.isfile(url_path):
                        # Can not send a download link to the user if the file is stored locally without url config
                        bot.send_message(
                            chat_id=update.effective_chat.id,
                            text='The file was to big to sent or for some reason could not be sent directly. Another '
                                 'way of sending the file was not configured by the adminstrator. You can use /support '
                                 'to contact the admins.')
                        return

                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Download', url=url_path), ], ])
                    bot.send_message(
                        chat_id=update.effective_chat.id,
                        text='File was either too big for Telegram or could for some reason not be sent directly, '
                             'please use this download button',
                        reply_markup=keyboard)

                self.current_menu.pop(user_id, None)
                self.keyboard_message_id.pop(user_id, None)
                self.video_information.pop(user_id, None)

    def menu_change(self, bot: Bot, update: Update):
        """Menu changes

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        user_id = update.callback_query.from_user.id
        text = update.callback_query.data

        keyboard = self.get_keyboard(text, self.video_information[user_id])
        bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=self.keyboard_message_id[user_id].message_id,
            reply_markup=keyboard)

        self.current_menu[user_id] = text

    def abort(self, bot: Bot, update: Update):
        """Abort

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
        """
        user_id = update.effective_user.id
        text = 'Aborted {}'.format(self.video_information[user_id]['title'])
        if update.callback_query:
            update.callback_query.answer(text=text)
            bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=self.keyboard_message_id[user_id].message_id,
                reply_markup=[])
        else:
            bot.send_message(chat_id=update.effective_chat.id, text=text)

        self.current_menu.pop(user_id, None)
        self.keyboard_message_id.pop(user_id, None)
        self.video_information.pop(user_id, None)

    def get_keyboard(self, keyboard_name: str, video_information: dict) -> InlineKeyboardMarkup:
        """Get inline keyboard list

        Args:
            keyboard_name (:obj:`str`): For available names look in the description for current_menu
            video_information (:obj:`dict`): Information about the video

        Returns:
            :class:`telegram.inline.inlinekeyboardmarkup.InlineKeyboardMarkup`: InlineKeyboardMarkup with the new menu
        """
        formats = {}
        if video_information.get('formats', None):
            for format_ in video_information['formats']:
                formats[format_['format_id']] = {
                    'ext': format_.get('ext', None),
                    'video': format_['vcodec'] if format_.get('vcodec', None) != 'none' else None,
                    'audio': format_['acodec'] if format_.get('acodec', None) != 'none' else None,
                    'filesize': format_.get('filesize', None),
                    'res':
                        '%sx%s' % (format_['width'], format_['height'])
                        if format_.get('height', None) and format_.get('width', None)
                        else None,
                    'vcodec': format_.get('vcodec', None),
                    'acodec': format_.get('acodec', None),
                    'abr': '%sk' % format_['abr'] if format_.get('abr', None) else None,
                }

        keyboard = []
        if keyboard_name == 'format':
            if formats:
                if [format_ for format_ in formats.values() if format_['audio']]:
                    keyboard.append([InlineKeyboardButton('Audio Only', callback_data='audio'), ])
                if [format_ for format_ in formats.values() if format_['video']]:
                    keyboard.append([InlineKeyboardButton('Video Only', callback_data='video'), ])
            keyboard.append([InlineKeyboardButton('Video + Audio', callback_data='video_audio'), ])

        elif keyboard_name in ['video', 'audio', 'video_audio']:
            name = keyboard_name.title().replace('_', ' + ')
            keyboard = [[
                InlineKeyboardButton('Best {}'.format(name), callback_data='download {} best'.format(keyboard_name)),
            ], ]
            if formats:
                keyboard.append([InlineKeyboardButton('Advanced', callback_data='{}_quality'.format(keyboard_name)), ])
        elif keyboard_name.endswith('_quality'):
            name = keyboard_name.replace('_quality', '')
            keyboard = self.get_advance_keyboard('{}'.format(name), formats)

        menu_structure = {
            'format': 'abort',
            'video': 'format',
            'audio': 'format',
            'video_audio': 'format',
            'video_quality': 'video',
            'audio_quality': 'audio',
            'video_audio_quality': 'video_audio',
        }

        if keyboard_name == 'format':
            keyboard.append([InlineKeyboardButton('Abort', callback_data=menu_structure[keyboard_name]), ])
        else:
            keyboard.append([InlineKeyboardButton('Back', callback_data=menu_structure[keyboard_name]), ])

        return InlineKeyboardMarkup(keyboard)

    def get_advance_keyboard(self, advance_menu: str, formats: dict) -> list:
        """Get advanced keyboard for audio, video or audio + video

        Args:
            advance_menu (:obj:`str`): Which menud you want audio, video or video_audio
            formats (:obj:`dict`): Dict with the format information
        Returns:
            :obj:`list`: List of lists containing :class:`telegram.inline.inlinekeyboardbutton.InlineKeyboardButton`
        """
        keyboard = []

        for format_id, format_ in formats.items():
            if (advance_menu == 'audio' and format_['video']) or \
                    (advance_menu == 'video' and format_['audio']) or \
                    (advance_menu == 'video_audio' and (not format_['video'] or not format_['audio'])):
                continue

            text = ''
            for key, value in format_.items():
                if key not in ['video', 'filesize', 'audio'] and value not in ['none', ] and value:
                    text += '{key}: {value} '.format(key=key, value=value)
            text = text.strip()
            keyboard.append(
                [InlineKeyboardButton(text=text, callback_data='download {} {}'.format(advance_menu, format_id)), ]
            )
        return keyboard


video_downloader = VideoDownloader()
