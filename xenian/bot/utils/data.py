import json
from pathlib import Path

from xenian.bot import settings

__all__ = ["data"]


class Data:
    """Class for managing simple persistent data"""

    def __init__(self):
        self.data_dir = settings.CONFIG_PATH / "persistent"
        self.data_dir.mkdir(exist_ok=True)

    def save(self, name: str, data: dict):
        """Save object to json

        Args:
            name (:obj:`str`): Name of data object
            data (:obj:`object`): JSON serializable data object
        """
        path = self.data_dir / (Path(name).stem + ".json")
        try:
            data = self.serialize(dict(data))
        except TypeError:
            pass

        path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            )
        )

    def get(self, name: str) -> dict:
        """Get data by name

        Args:
            name (:obj:`str`): Name of data object

        Returns:
            Object saved in the data file
        """
        path = self.data_dir / (Path(name).stem + ".json")
        if not path.is_file():
            data = {}
        else:
            data = json.loads(path.read_text())

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
                new_key = "{}--int".format(key)
            elif isinstance(key, float):
                new_key = "{}--float".format(key)
            elif not isinstance(key, str):
                raise ValueError("Key must be either str, int or float: {} {}".format(key, value))

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
            if key.endswith("--int"):
                new_key = int(key.replace("--int", ""))
            elif key.endswith("--float"):
                new_key = float(key.replace("--float", ""))

            if isinstance(value, dict):
                new_dict[new_key] = self.deserialize(value)
            else:
                new_dict[new_key] = value
        return new_dict


data = Data()
