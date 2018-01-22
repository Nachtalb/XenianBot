import urbandictionary as ud
from emoji import emojize
from telegram import Bot, ParseMode, Update

from xenian_bot.commands import BaseCommand

__all__ = ['urban_dictionary']


class UrbanDictionary(BaseCommand):
    """Urban Dictionary integration into this bot
    """

    def __init__(self):
        self.commands = [
            {
                'title': 'Urban Dictionary Definition',
                'description': 'Define a word or a sentence via urban dictionary',
                'command': self.define,
                'options': {
                    'pass_args': True
                },
                'args': 'WORD(S)'
            }
        ]

        self.e_thumbs_up = emojize(':thumbsup:', use_aliases=True)
        self.e_thumbs_down = emojize(':thumbsdown:', use_aliases=True)
        super(UrbanDictionary, self).__init__()

    def define(self, bot: Bot, update: Update, args: list = None):
        """Search in urban dictionary

        Args:
            bot (:obj:`telegram.bot.Bot`): Telegram Api Bot Object.
            update (:obj:`telegram.update.Update`): Telegram Api Update Object
            args (:obj:`list`, optional): List of sent arguments
        """
        if update.message.reply_to_message is not None:
            return
        word = update.message.text
        if args:
            word = ' '.join(args)

        definitions = ud.define(word)

        if not definitions:
            update.message.reply_text('Could not find anything for: %s' % update.message.text)
            return
        best = definitions[0]
        reply = """*Definition for [{word}]*

{definition}

*Example*

{example}

*Votes*
{emoji_up} {upvotes} | {emoji_down} {downvotes}
        """.format(
            word=best.word,
            definition=best.definition,
            example=best.example,
            upvotes=best.upvotes,
            downvotes=best.downvotes,
            emoji_up=self.e_thumbs_up,
            emoji_down=self.e_thumbs_down
        )
        reply = emojize(reply, use_aliases=True)
        update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


urban_dictionary = UrbanDictionary()
