from threading import Lock
from typing import Iterable

from mongoengine import DictField, Document, ListField, ReferenceField
from mongoengine.base import BaseField
from telegram import Bot, TelegramObject

__all__ = ['TelegramDocument']


class TelegramDocument(Document):
    _tg_object = None
    _bot = None
    meta = {'abstract': True}

    save_lock = Lock()

    class Meta:
        original = NotImplemented
        load_self = None
        pk_name = 'id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Meta.pk_name = getattr(self.Meta, 'pk_name', TelegramDocument.Meta.pk_name)
        self.Meta.load_self = getattr(self.Meta, 'load_self', TelegramDocument.Meta.load_self)
        if getattr(self.Meta, 'original', None) is None:
            raise NotImplementedError('You have to define original which tells me the original Telegram Object.')

    def __call__(self, bot: Bot):
        self._bot = bot
        return self

    def save(self, *args, **kwargs):
        try:
            self.save_lock.acquire()
            super().save(*args, **kwargs)
        finally:
            self.save_lock.release()

    @classmethod
    def fields(cls):
        return dict(filter(lambda item: isinstance(item[1], BaseField), cls.__dict__.items()))

    def _load_self(self, bot: Bot = None, force_update=False):
        """Load original telegram object

        Ways to do so:
            1. If `self.Meta.load_self` is set and the the argument `bot` has been given, then run the method on the
                bot object named after the string from `load_self` with the this objects pk as first argument. If the
                bot is not given fallback to 2.

            2. Check if current class has the attribute `original_object`, which must be a DictField containing the
                originals object ouptput from `obj.to_dict()`. With this information and `self.Meta.original`, which is
                the Telegram objects class, the object will be created. If `original_object` doesn't exist or
                `self.Meta.original` is not set fallback to 2.1.

                2.1. If the above did not work we try to use the `de_json` function on the TelegramObjects to get the object
                    we want. In the case that this still fails we fall back to method to 3.

            3. If `self.Meta.original` is available create an object from all the fields on self. Conveniently
                TelegramObjects just discard arguments and keyword arguments which it does not no. And so it will
                work even if there are fields that do not exist on the actual object.

        Args:
            bot (:object:`telegram.bot.Bot`, optional): The bot object which must be given if method one should be used.
                If it is not given method 1 described above can not be used and method 2 & 3 will be. The bot will be
                set on the created object as `.bot`.
            force_update (:object:`bool`, optional): Force load the with `self.Meta.load_self`. If this is not possible
                fall back to method 2 & 3. Instead of just returning `self._tg_object`. Defaults to `False`.

        Returns:
            (:obj:`TelegramObject` | None): The created Telegram object or none if it was not possible
        """
        self._bot = bot or self._bot
        if not force_update and self._tg_object:
            return self._tg_object

        if self.Meta.load_self is not None and self._bot is not None:
            method_name = self.Meta.load_self
            method = getattr(self._bot, method_name)
            self._tg_object = method(self.pk)
            return self._tg_object

        if hasattr(self, 'original_object') and self.Meta.original:
            try:
                self._tg_object = self.Meta.original(**self.original_object)
            except TypeError:
                try:
                    self._tg_object = self.Meta.original.de_json(self.original_object, self._bot)
                except AttributeError:
                    pass
            finally:
                if self._tg_object:
                    self._tg_object.bot = bot
                    return self._tg_object

        if self.Meta.original:
            data = {}
            for name, field in self.fields().items():
                value = getattr(self, name, None)

                if value is not None:
                    data[name] = value
            try:
                self._tg_object = self.Meta.original(**data)
                self._tg_object.bot = self._bot
                return self._tg_object
            except Exception:
                return None

    def to_object(self, bot: Bot):
        return self._load_self(bot=bot)

    @property
    def object(self):
        return self._load_self()

    def self_update(self, bot: Bot):
        return self._load_self(bot=bot, force_update=True)

    @staticmethod
    def _get_dict_from_object(self_cls, object: TelegramObject):
        data = {}
        for name, field in self_cls.fields().items():
            value = getattr(object, name, None)
            if value is None:
                continue
            elif isinstance(value, TelegramObject) \
                    and isinstance(field, ReferenceField) \
                    and TelegramDocument in field.document_type.__bases__:
                value = field.document_type.from_object(value)
            elif isinstance(value, Iterable) \
                    and isinstance(field, ListField) \
                    and isinstance(next(iter(value), None), TelegramObject) \
                    and isinstance(field.field, DictField):
                value = list(map(lambda item: item.to_dict(), value))
            data[name] = value
        return data

    def self_from_object(self, object: TelegramObject):
        if hasattr(object, 'bot') and isinstance(object.bot, Bot):
            self._bot = object.bot

        for key, value in self._get_dict_from_object(self, object).items():
            self.__setattr__(key, value)

        if hasattr(self, 'original_object') and isinstance(self._fields.get('original_object'), DictField):
            self.original_object = object.to_dict()

    @classmethod
    def from_object(cls, obj: TelegramObject, use_pk: bool = True, **query):
        if use_pk:
            pk_name = getattr(cls.Meta, 'pk_name', TelegramDocument.Meta.pk_name)
            query.update({'pk': getattr(obj, pk_name, None)})

        doc = cls.objects(**query).first()
        if doc is None:
            doc = cls()
        doc.self_from_object(obj)
        return doc
