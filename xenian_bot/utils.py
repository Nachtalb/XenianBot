import os, json
from codecs import open as copen


class Data:

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
        with copen(path, mode='w', encoding='utf-8') as data_file:
            json.dump(data, data_file, ensure_ascii=False, indent=4, sort_keys=True)

    def get(self, name: str):
        """Get data by name

        Args:
            name (:obj:`str`): Name of data object
        """
        name = os.path.splitext(os.path.basename(name))[0]
        path = os.path.join(self.data_dir, name + '.json')
        if not os.path.isfile(path):
            os.mknod(path, 0o644)
        with copen(path, encoding='utf-8') as data_file:
            content = data_file.read()
            content = content or '{}'
            return json.loads(content)


data = Data()
