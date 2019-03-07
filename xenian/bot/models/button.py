from mongoengine import BooleanField, DictField, Document, StringField


class Button(Document):
    text = StringField()
    callback = StringField()

    data = DictField()
    url = StringField()

    prefix = StringField()

    confirmation_requred = BooleanField(default=False)
    abort_callback = StringField()

    def callback_data(self, answer: bool = None) -> str:
        suffix = ''
        if isinstance(answer, bool):
            suffix = f':{1 if answer else 0}'
        return f'{self.prefix}:{self.id}{suffix}'

    def extract_answer(self, callback_data: str) -> bool or None:
        _, answer = callback_data.rsplit(':', 1)

        if answer == str(self.id):
            return None

        return answer == '1'
