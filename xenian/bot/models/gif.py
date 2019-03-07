from mongoengine import DictField, Document, IntField, StringField

__all__ = ['Gif']


class Gif(Document):
    meta = {'collection': 'gifs'}

    file_id = StringField()
    thumb = DictField()
    file_name = StringField()
    mime_type = StringField()
    file_size = IntField()
    width = IntField(default=None)
    height = IntField(default=None)
    duration = IntField(default=None)
