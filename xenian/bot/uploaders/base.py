class UploaderBase:
    """Base class for other uploader's to inherit from, to ensure to use the same methods and attributes.

    Attributes:
        configuration (:obj:`dict`): Configuration of this uploader
    Args:
        configuration (:obj:`dict`): Configuration of this uploader
        connect (:obj:`bool`, optional): If the uploader should directly connect to the server
    """

    _mandatory_configuration = {}
    """(:obj:`dict`): Mandatory configuration settings.

    Usage:
        {'some_key': type}:
            - 'some_key' is a key name like 'host'
            - type is a python object like :class:`str`
    """

    def __init__(self, configuration: dict, connect: bool = False):
        for key, type_ in self._mandatory_configuration.items():
            if key not in configuration:
                raise KeyError('Configuration must contain key: "%s"' % key)
            if not isinstance(configuration[key], type_):
                raise TypeError('Configuration key "%s" must be instance of "%s"' % (key, type_))

        self.configuration = configuration
        if connect:
            self.connect()

    def connect(self):
        """Connect to the server defined in the configuration"""
        pass

    def close(self):
        """Close connection to the server"""
        pass

    def upload(self, file, remove_after: int):
        """Upload a file to the server

        Args:
            file: file like object or a path to a file
            remove_after (:obj:`int`): After how much time to remove the file in sec

        Raises:
            :obj:`NotImplementedError`: If you did not implement the function in your uploader.
        """
        raise NotImplementedError

    def remove(self, file_path: str, self_connect: bool):
        """Remove a file from the server

        Args:
            file_path (:obj:`str`): path to a file
            self_connect (:obj:`bool`): If he method should connect to the server by itself

        Raises:
            :obj:`NotImplementedError`: If you did not implement the function in your uploader.
        """
        raise NotImplementedError
