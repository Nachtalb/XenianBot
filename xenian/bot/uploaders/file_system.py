import os
import subprocess
import warnings

import xenian.bot
from xenian.bot.utils import CustomNamedTemporaryFile
from .base import UploaderBase


class FileSystemUploader(UploaderBase):
    """Save files on file system
    """

    _mandatory_configuration = {'path': str}

    def upload(self, file, filename: str = None, save_path: str = None, remove_after: int = None):
        """Upload file to the ssh server

        Args:
            file: Path to file on file system or file like object. If a file path is given the file is copied to the new
                place not moved.
            filename (:obj:`str`, optional): New filename, must be set if file is a file like object
            save_path (:obj:`str`, optional): Directory where to save the file. Joins with the configurations path.
                Creates directory if it does not exist yet.
            remove_after (:obj:`int`, optional): After how much time to remove the file in sec.
                Defaults to None (do not remove)
        """
        is_file_object = bool(getattr(file, 'read', False))
        if is_file_object:
            if filename is None:
                raise ValueError('filename must be set when file is a file like object')
            with CustomNamedTemporaryFile(delete=False) as new_file:
                file.seek(0)
                new_file.write(file.read())
                new_file.save()

                real_file = new_file.name
                filename = filename
        else:
            real_file = file
            filename = filename or os.path.basename(real_file)

        save_dir = os.path.join(self.configuration['path'], save_path) if save_path else \
            self.configuration['path']
        save_path = os.path.join(save_dir, filename)
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.realpath(save_path)
        real_file = os.path.realpath(real_file)
        if os.name == 'nt':
            copy_outcome = subprocess.call(['copy', real_file, save_path], shell=True)
            chmod_outcome = 0
        else:
            copy_outcome = subprocess.call(['cp', real_file, save_path])
            chmod_outcome = subprocess.call(['chmod', '644', save_path])

        if copy_outcome != 0:
            raise IOError(f'Copying file from {real_file} to {save_path} did not work.')

        if chmod_outcome != 0:
            warnings.warn(f'Could not set permissions for "{save_path}".')

        if remove_after:
            xenian.bot.job_queue.run_once(
                callback=lambda bot, job: self.remove(save_path, True),
                when=remove_after,
                name='Remove file locally: {}'.format(save_path))

        if is_file_object:
            os.unlink(real_file)

    def remove(self, file_path: str, self_connect: bool):
        """Remove a file from the server

        Args:
            file_path (:obj:`str`): path to a file
            self_connect (:obj:`bool`): If he method should connect to the server by itself

        Raises:
            :obj:`NotImplementedError`: If you did not implement the function in your uploader.
        """
        if self_connect:
            self.connect()

        os.unlink(file_path)

        if self_connect:
            self.close()
