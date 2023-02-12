import os
from typing import IO

from telegram import InputMediaPhoto, PhotoSize


class Post:
    class PostDictWrapper:
        post = {}

        def __getattribute__(self, item):
            return self.post.get("")

    def __init__(
        self,
        post: dict,
        media: str | IO | PhotoSize | None = None,
        caption: str | None = None,
        post_url: str | None = None,
    ):
        self.post = post
        self.post_url = post_url
        self._telegram = InputMediaPhoto(media, caption)
        self._file = None

    def is_image(self, include_gif: bool = False) -> bool | None:
        if self.file_extension is None:
            return

        image_extensions = ["jpg", "jpeg", "png"]
        if include_gif:
            image_extensions.append("gif")
        return self.file_extension in image_extensions

    def is_video(self, include_gif: bool = True) -> bool | None:
        if self.file_extension is None:
            return

        video_extensions = ["webm", "mp4"]
        if include_gif:
            video_extensions.append("gif")
        return self.file_extension in video_extensions

    @property
    def file_extension(self):
        media = self.media
        if isinstance(media, PhotoSize):
            if self._file is None:
                self._file = media.get_file()
            media = self._file.file_path

        if isinstance(media, str):
            split = os.path.splitext(self.media)  # type: ignore
            if len(split) != 2:
                return
            return split[1].lstrip(".")
        return

    @property
    def media(self) -> str | IO | PhotoSize:
        return self.telegram.media  # type: ignore

    @media.setter
    def media(self, value: str | IO | PhotoSize):
        self.telegram.media = value

    @property
    def caption(self) -> str:
        return self.telegram.caption

    @caption.setter
    def caption(self, value: str):
        self.telegram.caption = value

    @property
    def telegram(self) -> InputMediaPhoto:
        return self._telegram

    @telegram.setter
    def telegram(self, value: InputMediaPhoto or str or tuple or list):
        actual_value = None
        if isinstance(value, InputMediaPhoto):
            actual_value = value
        elif (isinstance(value, tuple) or isinstance(value, list)) and len(value) == 2:
            actual_value = InputMediaPhoto(*value)  # type: ignore
        elif isinstance(value, str):
            if self._telegram:
                actual_value = self._telegram
                actual_value.media = value
            else:
                actual_value = InputMediaPhoto(value)
        if not actual_value:
            raise ValueError("Value must either be a tuple/list, dict, InputMediaPhoto or str")

        self._telegram = actual_value


class PostError(Exception):
    IMAGE_NOT_FOUND = 0
    WRONG_FILE_TYPE = 10
    UNDEFINED_ERROR = 20

    def __init__(self, code: int, post: Post | None = None):
        self.code = code
        self.post = post
