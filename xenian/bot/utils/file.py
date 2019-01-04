import os

import requests

from xenian.bot.settings import UPLOADER
from xenian.bot.uploaders import uploader
from xenian.bot.utils.temp_file import CustomNamedTemporaryFile

__all__ = ['download_file_from_url', 'download_file_from_url_and_upload', 'upload_image']


def upload_image(image_file, target_file_name: str = None, remove_after: int = None) -> str:
    """Upload the given image to the in the settings specified place.

    Args:
        image_file: File like object of an image or path to an image
        target_file_name (:obj:`str`, optional): Name of the given file. Can be left empty if image_file is a file path
        remove_after (:obj:`int`, optional): After how much time to remove the file in sec. Do not remove by default

    Returns:
        :obj:`str`: Url to the uploaded image
    Raises:
        ValueError: If the image_file is an file like object and the file_name has not been set.
    """
    if not target_file_name:
        if not isinstance(image_file, str):
            error_message = 'When image_file is a file like object the file_name must be set.'
            raise ValueError(error_message)
        target_file_name = os.path.basename(image_file)

    uploader.connect()
    uploader.upload(image_file, target_file_name, remove_after=remove_after)
    uploader.close()

    path = UPLOADER.get('url', None) or UPLOADER['configuration'].get('path', None) or ''
    return os.path.join(path, target_file_name)


def download_file_from_url(url: str) -> str:
    """Download a file from an url

    Args:
        url (:obj:`str`): URL to the file

    Returns:
        (:obj:`str`): Path to the download file.

    """
    with CustomNamedTemporaryFile(delete=False, mode='wb') as file_:
        response = requests.get(url, allow_redirects=True)
        file_.write(response.content)
        file_.close()
        return file_.name


def download_file_from_url_and_upload(url: str, target_file_name: str = None, remove_after: int = None) -> str:
    """Download a file from an url

    Args:
        url (:obj:`str`): URL to the file
        target_file_name (:obj:`str`, optional): Name of the given file. Can be left empty if image_file is a file path
        remove_after (:obj:`int`, optional): After how much time to remove the file in sec. Do not remove by default

    Returns:
        (:obj:`str`): Path to the download file.

    """
    url = url.rstrip('/')
    if not target_file_name:
        target_file_name = os.path.basename(url)

    downloaded_file = download_file_from_url(url)
    return upload_image(downloaded_file, target_file_name=target_file_name, remove_after=remove_after)
