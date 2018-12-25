Xenian Bot
==========

`@XenianBot <https://t.me/XenianBot>`__ \|
`GitHub <https://github.com/Nachtalb/XenianBot>`__

.. contents:: Table of Contents


What I do
---------

I am a personal assistant which can do various tasks for you. For example, I can do reverse image searches directly here
in Telegram. To see my full capability, send me ``/commands`` and you will see everything available or go to
`Commands <#commands>`__.

If you like this bot you can rate it `here <https://telegram.me/storebot?start=xenianbot>`__.

Commands
--------

Direct Commands:
~~~~~~~~~~~~~~~~

Base Group
^^^^^^^^^^

-  ``/start`` - Initialize the bot
-  ``/commands`` - Show all available commands
-  ``/support`` - Contact bot maintainer for support of any kind
-  ``/contribute <text>`` - Send the supporters and admins a request of any kind
-  ``/error <text>`` - If you have found an error please use this command.
-  ``/help`` - Show all available commands

Custom
^^^^^^

-  ``/db_save_mode <tag>`` - Start database save mode and send your objects
-  ``/db_save <tag>`` - Reply to save an object to a custom database
-  ``/db_info`` - Show created databases
-  ``/db_delete`` - Delete selected database
-  ``/db_list`` - List the content of a DB

Anime
^^^^^

-  ``/random`` - Send random anime GIF
-  ``/danbooru_search <tag_1> <tag_2> <page=page_num> <limit=limit>`` - Search on danbooru by max 2 tags separated by comma. You can define which page (default 0) and the limit (default 5, max 100)
-  ``/danbooru_latest <page=page_num> <limit=limit>`` - Get latest uploads from danbooru you can use the options page (default 0) and limit (default 5, max 100)

Misc
^^^^

-  ``/define <text>`` - Define a word or a sentence via urban dictionary
-  ``/roll <min> <max>`` - Roll a number between 0 and 6 or give me another range
-  ``/decide`` - Yes or No
-  ``/maths`` - Show all available math functions
-  ``/calc <equation>`` - Solve an equation you send me, all math functions can be seen with /maths
-  ``/tts <text> <-l LANG>`` - Convert text the given text or the message replied to, to text. Use `-l` to define a language, like de, en or ru
-  ``/translate <text> <-lf LANG> <-lt LANG>`` - Translate a reply or a given text from `-lf` (default: detect) language to `-lt` (default: en) language

Download
^^^^^^^^

-  ``/download_mode`` - If on download stickers and gifs sent to the bot of off reverse search is reactivated. Does not work in groups
-  ``/zip_mode`` - If zip mode is on collect all downloads and zip them upon disabling zip mode
-  ``/download`` - Reply to media for download

Image
^^^^^

-  ``/search`` - Reply to media for reverse search
-  ``/itt <-l LANG>`` - Extract text from images
-  ``/itt_translate <text> <-lf LANG> <-lt LANG>`` - Extract text from images and translate it. `-lf` (default: detect, /itt_lang) language on image, to `-lt` (default: en, normal language codes) language.
-  ``/itt_lang`` - Available languages for Image to Text

Group Management
^^^^^^^^^^^^^^^^

-  ``/ban`` - Ban a user. Reply to one of his messages with this command (Group Only)
-  ``/warn`` - Warn a user, after 3 warnings he get banned. Reply to one of his messages with this command (Group Only)
-  ``/kick <time>`` - Kick a user for 10 min or give a specific amount of time (in min) between 30sec (0.5 min) and 366 days (527040 min). Reply to one of his messages with this command (Group Only)
-  ``/delete`` - Delete a message from a user and warn them. Reply to one of his messages with this command (Group Only)
-  ``/unwarn`` - Remove all warnings from a User. Reply to one of his messages with this command (Group Only)
-  ``/rules`` - Show rules for this group (Group Only)
-  ``/rules_define <text>`` - Define rules for this group (Group Only)
-  ``/rules_remove`` - Remove rules for this group (Group Only)


Indirect Commands:
~~~~~~~~~~~~~~~~~~

Custom
^^^^^^

-  **Save object** - Send objects while /save_mode is turned of to save them into your defined db

Download
^^^^^^^^

-  **Download Stickers** - Turn on /download_mode and send stickers
-  **Download Gifs** - Turn on /download_mode and send videos and gifs
-  **Video from URL** - Turn on /download_mode and send links to videos like a youtube video

Image
^^^^^

-  **Auto Search** - Turn off /download_mode and send some kind of media file.

Misc
^^^^

-  **Calculator** - Solve equations you send me, to get a full list of supported math functions use /maths (PRIVATE CHAT ONLY)


Contributions
-------------

Bug report / Feature request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have found a bug or want a new feature, please file an issue on GitHub `Issues <https://github.com/Nachtalb/python_telegram_bot_template/issues>`__

Code Contribution / Pull Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please use a line length of 120 characters and `Google Style Python Docstrings <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`__.

Development
~~~~~~~~~~~

For the project I choose `buildout <http://www.buildout.org/en/latest/contents.html>`__ instead of the default pip way.
I manly did this because it makes installation easier. I recommend to be in an virtualenv for any project, but this is
up to you. Now for the installation:

.. code:: bash

   ln -s development.cfg buildout.cfg
   python bootstrap.py
   bin/buildout

And everything should be installed. Now you can copy and configure your settings. For this you need an Telegram Bot API
Token > `@BotFather <https://t.me/BotFather>`__. The ``settings.py`` should be self explanatory.

.. code:: bash

   cp xenian.bot/settings.example.py  xenian.bot/settings.py

To run the bot simply run

.. code:: bash

   bin/bot

Command Concept
^^^^^^^^^^^^^^^

I am still working on how I want to make the commends to be used as easily as possible. At the moment this is how it works:

In the folder ``python_telegram_bot_template/commands/`` you’ll find a ``__init__.py``, ``base.py`` and ``builtins.py``.
The ``base.py`` contains the base command, which is used for every other command. It has the following attributes:

all_commands
    This is a variable containing all the commands which you create with this class as Parent. If you override the
    ``__init__`` method you have to call super init otherwise, the command will not be added to this list. This list is
    used for adding the commands as handlers for telegram and for creating the commands list.
commands
    This is a list of dictionaries in which you can define commands. This list contains the following keys:

    title (optional)
        If no title given the name of the command function is taken (underscores replaced with space and the first word
        is capitalized)A string for a title for the command. This does not have to be the same as the ``command_name``.
        Your ``command_name`` could be eg. ``desc`` so the command would be ``/desc``, but the title would be
        ``Describe``. Like this, it is easier for the user to get the meaning of function from a command directly from
        the command list. - ``description`` (optional): Default is an empty string. As the name says, this is the
        description. It is shown on the command list. Describe what your command does in a few words.

    command_name (optional)
        Default is the name of the given command function. This is what the user has to run So for the start command it
        would be ``start``. If you do not define one yourself, the lowercase string of the name of your class is taken.

    command (mandatory)
        This is the function of the command. This has to be set.

    handler (optional)
        Default is the CommandHandler. This is the handler your command uses. This could be ``MessageHandler``,
        ``CommandHandler`` or any other handler.

    options (optional)
        By default the callback and command are set. If you add another argument you do not have to define callback and
        command in the CommandHandler again and callback in the MessageHandler. This is a dict of arguments given to the
        handler.

    hidden (optional)
        Default is False. If True the command is hidden from the command list.

    args (optional)
        If you have args, you can write them here. Eg. a command like this: ``/add_human Nick 20 male`` your text would
        be like ``NAME AGE GENDER``.


After you create your class, you have to call it at least once. It doesn’t matter where you call it from, but I like to
just call it directly after the code, as you can see in the builtins.py. And do not forget that the file with the
command must be loaded imported somewhere. I usually do this directly in the ``__init__.py``.

A good example can be found in the ``reverse_image_search.py``: https://github.com/Nachtalb/XenianBot/blob/b482cbf8a1eb2ebe3f9683c9144bd3e222a26716/xenian.bot/commands/reverse_image_search.py#L23-L56

Uploaders Concept
^^^^^^^^^^^^^^^^^

Like for the commands I tried to make it easier to use different kinds of file storage. You can find a configuration in
the settings.py and the “uploaders” itself in the ``python_telegram_bot_template/uploaaders/`` folder. The goal is that
you can only change the configuration in the settings.py and your bot works without any further adjustment. So you could
use the local file system for local development and then switch to ssh for production, or something like this.

You get the uploader by
``from python_telegram_bot_template.uploaders import uploader``. If you use it you should always start with
``uploader.connect()`` then upload / save whatever you want with ``uploader.upload(...)`` and finally close the
connection with ``uploader.close()``. You should even use this if you are using the file system. It is to prevent errors
when you switch it someday in the future.

Now to the attributes and so on:

_mandatory_configuration
    It defines what must be in the configuration inside the settings.py. E.g. for the file system this is

.. code:: python

   {'path': str}

which means you have to define

.. code:: python

   UPLOADER = {
       'uploader': 'xenian.bot.uploaders.file_system.FileSystemUploader',  # What uploader to use
       'configuration': {
           'path': '/some/path/to/your/uploads',
       }
   }

If you are using the ssh uploader you have to define more:

.. code:: python

   {'host': str, 'user': str, 'password': str, 'upload_dir': str}

.. code:: python

   UPLOADER = {
       'uploader': 'xenian.bot.uploaders.ssh.SSHUploader',
       'configuration': {
           'host': '000.000.000.000',
           'user': 'chuck.norris',
           'password': 'i_am_immortal',
           'upload_dir': '/some/path/on/your/server/',
           'key_filename': '/home/chuck.norris/.ssh/id_rsa',  # This is not defined as mandatory because on most ssh
           # servers you don't only use the ssh key as authentication, but if you do define this configuration as well.
       }
   }

As you can see in the dict’s above it is always a name as key and a type as value. This is checked when you initialize
the uploader the first time.

configuration
    Filled in on the initialization from the uploader. It contains the configuration defined in the settings.py

Now to the methods:

__init__
    As always this initializes the uploader. If you need to override it, don’t forget to call super init otherwise,
    the configuration is not checked and applied.

connect
    Connect to the server / service or whatever. This method doesn’t need to be implemented. E.g. the file system didn’t
    need it.

close
    Close the connection to the server / service … This method too doesn’t have to be implemented.

uplaod
    In here you define the actual logic of the uploader. If you do not implement this method in your custom uploader
    there will be an ``NotImplementedError`` raised, when used.

Thank you for using `@XenianBot <https://t.me/XenianBot>`__.
