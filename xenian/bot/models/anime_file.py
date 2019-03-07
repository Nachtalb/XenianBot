from mongoengine import Document, StringField

__all__ = ['AnimeFile']


class AnimeFile(Document):
    meta = {'collection': 'files'}

    file_id = StringField()
    location = StringField()
