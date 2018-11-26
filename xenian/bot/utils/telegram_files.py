import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

from PIL import Image
from imageio.core import NeedDownloadError
from imageio import plugins
from telegram import Bot, Update, Message

from . import CustomNamedTemporaryFile

try:
    from moviepy.video.io.VideoFileClip import VideoFileClip
except NeedDownloadError as error:
    if 'ffmpeg.download()' in error.args[0]:
        plugins.ffmpeg.download()
    else:
        raise error

__all__ = ['image_download', 'sticker_download', 'video_download', 'video_to_gif', 'video_to_gif_download',
           'auto_download']


@contextmanager
def video_to_gif_download(bot: Bot, message: Message):
    """Download and convert a video to a gif

    Videos chosen in this order:
    1. Document objects sent (many videos / gifs are actually documents instead of video objects)
    2. Video objects
    3. Document objects in the message replied to
    4. Video objects in the message replied to

    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        message (:obj:`telegram.message.Message`): Telegram Api Message Object
    Returns:
        :obj:`str`: Path to gif file
    """
    with video_download(bot, message) as video_path:
        with video_to_gif(video_path) as gif_path:
            yield gif_path


@contextmanager
def video_to_gif(video_path: str):
    """Convert a video to a gif

    Args:
        video_path (:obj:`str`): The videos path
    Returns:
        :obj:`str`: Path to gif file
    """
    video_clip = VideoFileClip(video_path, audio=False)

    with NamedTemporaryFile(suffix='.gif') as gif_file:
        video_clip.write_gif(gif_file.name)

        dirname = os.path.dirname(gif_file.name)
        file_name = os.path.splitext(gif_file.name)[0]
        compressed_gif_path = os.path.join(dirname, file_name + '-min.gif')

        os.system('gifsicle -O3 --lossy=50 -o {dst} {src}'.format(dst=compressed_gif_path, src=gif_file.name))
        if os.path.isfile(compressed_gif_path):
            yield compressed_gif_path
        else:
            yield gif_file.name


@contextmanager
def video_download(bot: Bot, message: Message):
    """Download and convert a video to a gif

    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        message (:obj:`telegram.message.Message`): Telegram Api Message Object

    Returns:
        :obj:`str`: Path to gif file
    """
    document = message.document or message.video
    video = bot.getFile(document.file_id)

    with NamedTemporaryFile(suffix='.mp4') as video_file:
        video.download(video_file.name)

        yield video_file.name


@contextmanager
def sticker_download(bot: Bot, message: Message):
    """Download a sticker


    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        message (:obj:`telegram.message.Message`): Telegram Api Message Object

    Returns:
        :obj:`str`: Path to image file
    """
    sticker_image = bot.getFile(message.sticker.file_id)

    with CustomNamedTemporaryFile(suffix='.png') as image_file:
        sticker_image.download(out=image_file)
        image_file.close()
        pil_image = Image.open(image_file.name).convert("RGBA")
        pil_image.save(image_file.name, 'png')

        yield image_file.name


@contextmanager
def image_download(bot: Bot, message: Message):
    """Download an image


    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        message (:obj:`telegram.message.Message`): Telegram Api Message Object

    Returns:
        :obj:`str`: Path to image file
    """
    photo = bot.getFile(message.photo[-1].file_id)
    with NamedTemporaryFile(suffix='.png') as image_file:
        photo.download(out=image_file)
        yield image_file.name


@contextmanager
def auto_download(bot: Bot, update: Update, convert_video_to_gif: bool = False):
    """Auto download the correct file with the given message

    How the file to download is chosen:
    1. Does the message have a reply_to_message?
      Yes:
        Use reply_to_message further on
      No:
        Use sent message further on
    2. What type?:
      Photo:
        Use image downloader
      Sticker:
        Use sticker downloader
      Document or Video:
        Convert to Gif?
          Yes:
            Use function download and convert
          No:
            Use normal video downloader

    Args:
        bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
        update (:obj:`telegram.update.Update`): Telegram Api Update Object
        convert_video_to_gif (:obj:`bool`, optional): If the file is a video should it be converted to an gif
    """
    generator = None

    msg = update.message
    reply_to_msg = msg.reply_to_message if getattr(msg, 'reply_to_message') else msg

    if reply_to_msg is not msg:
        msg = reply_to_msg

    if msg.photo:
        generator = image_download
    elif msg.sticker:
        generator = sticker_download
    elif msg.document or msg.video:
        if convert_video_to_gif:
            generator = video_to_gif_download
        else:
            generator = video_download

    if generator:
        with generator(bot, msg) as file_path:
            yield file_path
    else:
        yield
