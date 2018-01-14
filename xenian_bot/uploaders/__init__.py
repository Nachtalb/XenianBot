from importlib import import_module

from python_telegram_bot_template.settings import UPLOADER

uploader_pkg_name, uploader_class_name = UPLOADER['uploader'].rsplit('.', 1)
uploader_module = import_module(uploader_pkg_name)
uploader_class = getattr(uploader_module, uploader_class_name)
uploader = uploader_class(UPLOADER['configuration'])


__all__ = ['uploader']
