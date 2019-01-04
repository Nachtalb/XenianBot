import io
import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from types import MethodType
from urllib.request import urlretrieve

from xenian.bot.settings import UPLOADER
from xenian.bot.uploaders import uploader

__all__ = ['save_file', 'CustomNamedTemporaryFile', 'download_file_from_url', 'download_file_from_url_and_upload',
           'upload_image']


@contextmanager
def CustomNamedTemporaryFile(delete=True, close=None, *args, **kwargs) -> _TemporaryFileWrapper:
    """A custom ``tempfile.NamedTemporaryFile`` to enable the following points

    - Save without closing the file
    - Close the file without it being deleted
    - Still have it be automatically delete on end of with statement or error along as ``delete`` is set to True

    Examples:
        Use as a normal ``tempfile.NamedTemporaryFile`` but save in between:

            >>> with CustomNamedTemporaryFile() as some_file:
            >>>     some_file.write('foo bar')
            >>>     some_file.save()
            >>>     other_function(some_file)

        Use as a normal ``tempfile.NamedTemporaryFile`` but close in between:
        This is useful eg. on windows. When the file is open on windows, other programs may not be permitted to access
        the file. In this case we want to close the file, without deleting it. Normally in this case we can set
        ``delete=False`` in the parameters. But then we would need to manually close it after the with statement.
        Even though this is useful it isn't without it's own risks. When you closed your file, but it is still open in
        somewhere else, the file can't be deleted on windows. You will get an "PermissionError: [WinError 32]" error.
        So make sure the file is closed.

            >>> with CustomNamedTemporaryFile() as some_file:
            >>>     some_file.write('foo bar')
            >>>     some_file.close()
            >>>     other_function(some_file.name)

        If you still want the file not being deleted automatically after the with statement, you can still set
        ``delete=False``.

            >>> with CustomNamedTemporaryFile(delete=False) as some_file:
            >>>     ...
            >>> print(some_file.closed)
            >>> # False

    Args:
        close (:obj:`bool`): If delete is set to false still close the file (no effect if delete is not set to false)
        Args are defiend in `tempfile.NamedTemporaryFile`
        Args are defiend in `tempfile.NamedTemporaryFile`
    Returns:
        :obj:`tempfile._TemporaryFileWrapper`:
    """
    file = NamedTemporaryFile(*args, **kwargs, delete=False)

    def delete_close():
        if delete:
            if not file.closed:
                file.close()
            if os.path.isfile(file.name):
                os.unlink(file.name)
        elif close is True:
            if not file.closed:
                file.close()

    file.__del__ = delete_close
    file.save = MethodType(save_file, file)

    try:
        yield file
    finally:
        delete_close()


def save_file(file: io.BufferedWriter):
    """Save file without closing it

    Args:
        file (:obj:`io.BufferedWriter`): A file-like object
    """
    file.flush()
    os.fsync(file.fileno())
    file.seek(0)


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
    with CustomNamedTemporaryFile(delete=False) as file_:
        file_.close()
        urlretrieve(url, file_.name)
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
