import os
from tempfile import NamedTemporaryFile

import paramiko

import xenian.bot
from .base import UploaderBase


class SSHUploader(UploaderBase):
    """Upload files to an ssh server via paramiko http://www.paramiko.org/

    Attributes:
        configuration (:obj:`dict`): Configuration of this uploader
        ssh (:obj:`paramiko.client.SSHClient`): Connection to the ssh server
        sftp (:obj:`paramiko.sftp_client.SFTPClient`): Connection via sftp to the ssh server
    Args:
        configuration (:obj:`dict`): Configuration of this uploader. Must contain these key: host, user, password,
            key_filename, upload_dir, ssh_authentication
        connect (:obj:`bool`, optional): If the uploader should directly connect to the server
    """

    _mandatory_configuration = {'host': str, 'user': str, 'password': str, 'upload_dir': str}

    def __init__(self, configuration: dict, connect: bool = False):
        self.ssh = None
        self.sftp = None

        super().__init__(configuration, connect)

    def connect(self):
        """Connect to the server defined in the configuration
        """
        self.ssh = paramiko.SSHClient()
        self.ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

        if self.configuration.get('key_filename', None):
            self.ssh.connect(self.configuration['host'],
                             username=self.configuration['user'],
                             password=self.configuration['password'],
                             key_filename=self.configuration['key_filename'])
        else:
            self.ssh.connect(self.configuration['host'],
                             username=self.configuration['user'],
                             password=self.configuration['password'])
        self.sftp = self.ssh.open_sftp()

    def close(self):
        """Close connection to the server
        """
        self.sftp.close()
        self.ssh.close()

    def upload(self, file, filename: str = None, upload_dir: str = None, remove_after: int = None):
        """Upload file to the ssh server

        Args:
            file: Path to file on file system or a file like object
            filename (:obj:`str`, optional): Filename on the server. This is mandatory if your file is a file like
                object.
            upload_dir (:obj:`str`, optional): Upload directory on server. Joins with the configurations upload_dir
            remove_after (:obj:`int`, optional): After how much time to remove the file in sec.
                Defaults to None (do not remove)
        """
        is_file_object = bool(getattr(file, 'read', False))
        if is_file_object:
            if filename is None:
                raise ValueError('filename must be set when file is a file like object')
            with NamedTemporaryFile(delete=False) as new_file:
                file.seek(0)
                new_file.write(file.read())

                real_file = new_file.name
                filename = filename
        else:
            real_file = file
            filename = filename or os.path.basename(real_file)

        upload_dir = os.path.join(self.configuration['upload_dir'], upload_dir) if upload_dir else \
            self.configuration['upload_dir']
        upload_path = os.path.join(upload_dir, filename)

        self.sftp.put(real_file, upload_path)

        if remove_after:
            xenian.bot.job_queue.run_once(
                callback=lambda bot, job: self.remove(upload_path, True),
                when=remove_after,
                name='Remove on server: {}'.format(upload_path))
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

        self.sftp.remove(file_path)

        if self_connect:
            self.close()
