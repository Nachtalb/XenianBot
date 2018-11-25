import json
import os
from codecs import open as copen

__all__ = ['data']


class Data:
    """Class for managing simple persistent data
    """

    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(dir_path, 'data')
        os.makedirs(self.data_dir, exist_ok=True)

    def save(self, name: str, data: object):
        """Save object to json

        Args:
            name (:obj:`str`): Name of data object
            data (:obj:`object`): JSON serializable data object
        """
        name = os.path.splitext(os.path.basename(name))[0]
        path = os.path.join(self.data_dir, name + '.json')
        try:
            data = self.serialize(dict(data))
        except TypeError:
            pass

        with copen(path, mode='w', encoding='utf-8') as data_file:
            json.dump(data, data_file, ensure_ascii=False, indent=4, sort_keys=True, )

    def get(self, name: object) -> object:
        """Get data by name

        Args:
            name (:obj:`str`): Name of data object

        Returns:
            Object saved in the data file
        """
        name = os.path.splitext(os.path.basename(name))[0]
        path = os.path.join(self.data_dir, name + '.json')
        if not os.path.isfile(path):
            os.mknod(path, 0o644)
        with copen(path, encoding='utf-8') as data_file:
            content = data_file.read()
            content = content or '{}'

            data = json.loads(content)
            if isinstance(data, dict):
                data = self.deserialize(data)
            return data

    def serialize(self, data: dict) -> dict:
        """Serialize a dict recursively

        Args:
            data (:obj:`dict`): Old dictionary

        Returns:
            :obj:`dict`: New dictionary

        Raises:
            ValueError: If key is not str, int or float
        """
        new_dict = {}
        for key, value in data.items():
            new_key = key
            if isinstance(key, int):
                new_key = '{}--int'.format(key)
            elif isinstance(key, float):
                new_key = '{}--float'.format(key)
            elif not isinstance(key, str):
                raise ValueError('Key must be either str, int or float: {} {}'.format(key, value))

            if isinstance(value, dict):
                new_dict[new_key] = self.serialize(value)
            else:
                new_dict[new_key] = value
        return new_dict

    def deserialize(self, data: dict) -> dict:
        """Deserialize a dict recursively

        Args:
            data (:obj:`dict`): Old dictionary

        Returns:
            :obj:`dict`: New dictionary

        Raises:
            ValueError: If key is not str, int or float
        """
        new_dict = {}
        for key, value in data.items():
            new_key = key
            if key.endswith('--int'):
                new_key = int(key.replace('--int', ''))
            elif key.endswith('--float'):
                new_key = float(key.replace('--float', ''))

            if isinstance(value, dict):
                new_dict[new_key] = self.deserialize(value)
            else:
                new_dict[new_key] = value
        return new_dict


data = Data()
