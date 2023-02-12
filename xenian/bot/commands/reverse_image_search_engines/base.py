import logging
import os
from urllib.parse import quote_plus

import requests
from telegram import InlineKeyboardButton

from xenian.bot.settings import UPLOADER
from xenian.bot.uploaders import uploader

__all__ = ["ReverseImageSearchEngine"]


class ReverseImageSearchEngine:
    """The base class for reverse image search engines to inherit from.

    Attributes:
        url_base (:obj:`str`): The base url of the image search engine eg. `https://www.google.com`
        url_path (:obj:`str`): The url path to the actual reverse image search function. The google url would look like
            this: `/searchbyimage?&image_url={image_url}`
        name (:obj:`str`): Name of thi search engine
        search_html (:obj:`str`): The html of the last searched image
        search_url (:obj:`str`): The image url of the last searched image

    Args:
        url_base (:obj:`str`): The base url of the image search engine eg. `https://www.google.com`
        url_path (:obj:`str`): The url path to the actual reverse image search function. It must contain `{image_url}`,
            in which the url to the image will be placed. The google url would look like this:
            `/searchbyimage?&image_url={image_url}`
        name (:obj:`str`, optional): Give the Search engine a name if you want
    """

    name = "Base Reverse Image Search Engine"
    logger = logging.getLogger(__name__)

    search_html = None
    search_url = None

    def __init__(self, url_base, url_path, name: str = ""):
        self.url_base = url_base
        self.url_path = url_path
        self.name = name

    def button(self, url):
        return InlineKeyboardButton(text=self.name.upper(), url=self.get_search_link_by_url(url))

    def get_search_link_by_url(self, url) -> str:
        """Get the reverse image search link for the given url

        Args:
            url (:obj:`str`): Link to the image

        Returns:
            :obj:`str`: Generated reverse image search engine for the given image
        """
        self.search_url = url
        self.search_html = ""
        return self.url_base + self.url_path.format(image_url=quote_plus(url))

    def get_search_link_by_file(self, file_) -> str:
        """Get the reverse image search link for the given file

        Args:
            file_: File like object

        Returns:
            :obj:`str`: Generated reverse image search engine for the given image
        """
        return self.get_search_link_by_url(self.upload_image(file_))

    def upload_image(self, image_file, file_name: str | None = None, remove_after: int | None = None) -> str:
        """Upload the given image to the in the settings specified place.

        Args:
            image_file: File like object of an image or path to an image
            file_name (:obj:`str`, optional): Name of the given file. Can be left empty if image_file is a file path
            remove_after (:obj:`int`, optional): After how much time to remove the file in sec. Defaults to None (do not remove)

        Returns:
            :obj:`str`: Url to the uploaded image
        Raises:
            ValueError: If the image_file is an file like object and the file_name has not been set.
        """
        if not file_name:
            if not isinstance(image_file, str):
                error_message = "When image_file is a file like object the file_name must be set."
                self.logger.warning(error_message)
                raise ValueError(error_message)
            file_name = os.path.basename(image_file)

        uploader.connect()
        uploader.upload(image_file, file_name, remove_after=remove_after)
        uploader.close()

        path = UPLOADER.get("url", None) or UPLOADER["configuration"].get("path", None) or ""
        return os.path.join(path, file_name)

    def get_html(self, url=None) -> str:
        """Get the HTML of the image search site.

        Args:
            url (:obj:`str`, optional): Link to the image, if no url is given it takes the last searched image url

        Returns:
            :obj:`str`: HTML of the image search site

        Raises:
            ValueError: If no url is defined and no last_searched_url is available
        """
        if not url:
            if not self.search_url:
                raise ValueError("No url defined and no last_searched_url available!")
            url = self.search_url
        if url == self.search_url and self.search_html:
            return self.search_html

        request = requests.get(self.get_search_link_by_url(url))
        self.search_html = request.text
        return self.search_html

    @property
    def best_match(self) -> dict:
        """Get info about the best matching image found

        Notes:
            This function must be individually made for every new search engine. This is because every search engine
            gives other data. Normally the return value should look something like this:
            ```
            {
                'thumbnail': str 'LINK_TO_THUMBNAIL',
                'website': str 'LINK_TO_FOUND_IMAGE',
                'website_name': str 'NAME_OF_WEBSITE_IMAGE_FOUND_ON',
                'size': {
                    'width': int 'IMAGE_WIDTH',
                    'height': int 'IMAGE_HEIGHT'
                },
                'similarity': float 'SIMILARITY_IN_%_TO_ORIGINAL'
            }
            ```

        Returns:
            :obj:`dict`: Dictionary of the found image

        Raises:
            NotImplementedError: If the method was not implemented
        """
        raise NotImplementedError
