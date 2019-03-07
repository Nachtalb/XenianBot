import urbandictionary as ud
from emoji import emojize
from telegram import Bot, ParseMode, Update

from xenian.bot.commands import BaseCommand

__all__ = ['urban_dictionary']


class UrbanDictionary(BaseCommand):
    """Urban Dictionary integration into this bot
    """

    group = 'Misc'

    def __init__(self):
        self.commands = [
            {
                'title': 'Urban Dictionary Definition',
                'description': 'Define a word or a sentence via urban dictionary',
                'command': self.define,
                'options': {
                    'pass_args': True
                },
                'args': ['text']
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
        if args:
            word = ' '.join(args)
        else:
            self.message.reply_text('You have to give me some text to search for.')
            return
        definitions = ud.define(word)

        if not definitions:
            self.message.reply_text('Could not find anything for: %s' % self.message.text)
            return
        best = definitions[0]
        reply = f"""*Urban Dictionary: [{best.word}]*

{best.definition}

*Example*

{best.example}

*Votes*
{self.e_thumbs_up} {best.upvotes} | {self.e_thumbs_down} {best.downvotes}
        """
        self.message.reply_text(emojize(reply, use_aliases=True), parse_mode=ParseMode.MARKDOWN)


urban_dictionary = UrbanDictionary()
