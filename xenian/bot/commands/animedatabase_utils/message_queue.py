from telegram import Message
from telegram.error import BadRequest, NetworkError, TimedOut

from xenian.bot.commands.animedatabase_utils.post import PostError


class MessageQueue:
    tag_limit = 6

    def __init__(self, total: int, message: Message, group_size: int = None):
        self.total = total
        self.message = message
        self.group_size = group_size or 1

        self.sent = 0
        self.errors = []

    def report(self, error: PostError = None):
        if error:
            self.errors.append(error)

        self.sent += 1
        if self.sent == self.total:
            self.finished()

    def finished(self):
        lines = []
        if self.message.chat.type not in ['group', 'supergroup']:
            lines.append('Images has been sent')

        if self.errors:
            error_codes = set(error.code for error in self.errors)
            if PostError.IMAGE_NOT_FOUND in error_codes:
                lines.append('Some files could not be retrieved')
                for error in filter(lambda e: e.code == PostError.IMAGE_NOT_FOUND and e.post.post_url, self.errors):
                    lines.append(f'- {error.post.post_url}')

            if PostError.WRONG_FILE_TYPE in error_codes and self.group_size > 1:
                lines.append('Videos were skipped because they cannot be sent via a group.')
                for error in filter(lambda e: e.code == PostError.WRONG_FILE_TYPE and e.post.post_url, self.errors):
                    lines.append(f'- {error.post.post_url}')

            if PostError.UNDEFINED_ERROR in error_codes:
                lines.append('Some files could not be sent')

        if lines:
            self.message.reply_text('\n'.join(lines),
                                    reply_to_message_id=self.message.message_id,
                                    disable_web_page_preview=True)

    @staticmethod
    def message_queue_exc_handler(argument_name: str):
        def wrapper(func, *args, **kwargs):
            def inner_wrapper(*args, **kwargs):
                queue = kwargs.get(argument_name)
                if not queue:
                    queues = [arg for arg in args if isinstance(arg, MessageQueue)]
                    if len(queues) > 1:
                        raise AttributeError('Got more than one MessageQueue\'s')
                    elif queues:
                        queue = queues[0]
                if not queue:
                    raise AttributeError('No MessageQueue found')
                try:
                    return func(*args, **kwargs)
                except (BadRequest, TimedOut, NetworkError) as e:
                    if isinstance(e, NetworkError) and 'The write operation timed out' not in e.message:
                        raise e

                    for item in range(queue.group_size):
                        queue.report(PostError(code=PostError.UNDEFINED_ERROR))

            return inner_wrapper

        return wrapper
