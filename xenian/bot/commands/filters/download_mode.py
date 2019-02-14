from telegram import Message
from telegram.ext import BaseFilter

from xenian.bot.utils import data

__all__ = ['download_mode_filter']


class DownloadMode(BaseFilter):
    """Filter which manages the download mode for each user

    Attributes:
        data_set_name (:obj:`str`): Name of file where this data is saved to.
    """
    data_set_name = 'download_mode'

    def filter(self, message: Message) -> bool:
        """Filter download_mode on or not

         Args:
            message (:class:`telegram.Message`): The message that is tested.

        Returns:
            :obj:`bool`
        """
        return self.is_mode_on(message.from_user.id)

    def is_mode_on(self, telegram_user: str) -> bool:
        """Check if mode is on

        Args:
            telegram_user (:obj:`str`): The telegram users user_id

        Returns:
            :obj:`bool`: True if the user has download mode on, False otherwise
        """
        mode_list = data.get(self.data_set_name)
        user_config = mode_list.get(telegram_user, {})
        if isinstance(user_config, bool):
            # Before user settings were a dict
            return user_config
        return user_config.get('on', False)

    def is_zip_mode_on(self, telegram_user: str) -> bool:
        """Check if zip is on

        Args:
            telegram_user (:obj:`str`): The telegram users user_id

        Returns:
            :obj:`bool`: True if the user has download mode and zip mode on, False otherwise
        """
        mode_list = data.get(self.data_set_name)
        user_config = mode_list.get(telegram_user, {})
        if isinstance(user_config, bool):
            # Before user settings were a dict
            return False

        return user_config.get('on') and user_config.get('zip')

    def turn_on(self, telegram_user: str, zip_mode: bool = False):
        """Turn download mode on

        Args:
            telegram_user (:obj:`str`): The telegram users user_id
            zip_mode: (:obj:`bool`): If the downloads shall be zipped
        """
        mode_dict = data.get(self.data_set_name)
        mode_dict[telegram_user] = {'on': True, 'zip': zip_mode}
        data.save(self.data_set_name, mode_dict)

    def turn_off(self, telegram_user: str):
        """Turn download mode off

        Args:
            telegram_user (:obj:`str`): The telegram users user_id
        """
        mode_dict = data.get(self.data_set_name)
        mode_dict[telegram_user] = {'on': False, 'zip': False}
        data.save(self.data_set_name, mode_dict)

    def toggle_mode(self, telegram_user: str, zip_mode: bool = False) -> bool:
        """Toggle download mode

        Args:
            telegram_user (:obj:`str`): The telegram users user_id
            zip_mode: (:obj:`bool`): If the downloads shall be zipped

        Returns:
                :obj:`bool`: True if the mode is now on False if off
        """
        if self.is_mode_on(telegram_user) or (zip_mode and self.is_zip_mode_on(telegram_user)):
            self.turn_off(telegram_user)
            return False
        self.turn_on(telegram_user, zip_mode)
        return True


download_mode_filter = DownloadMode()
