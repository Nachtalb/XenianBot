Changelog
=========

2.0.6 (unreleased)
------------------

- Added an alias command ``/help`` for ``/commands``


2.0.5 (2018-11-26)
------------------

- Fix error when saving a ``CustomNamedTemporaryFile`` file.
- Fix not being able to save sticker as image in sticker search
- Tell user that RIS is not working if the file path is not an url instead of just telling nothing
- Fix not working alias function
- Bump ``gTTS-token`` version to fix TTS
- Fix file type when saving ``voices``


2.0.4 (2018-11-26)
------------------

- Fix file permissions for copied files under unix systems


2.0.3 (2018-11-26)
------------------

- Fix file copying on unix devices


2.0.2 (2018-11-26)
------------------

-  Fix ``/commands raw`` command not working


2.0.1 (2018-11-26)
------------------

-  Fix paths in settings template


2.0.0 (2018-11-26)
------------------

Added
~~~~~

-  Custom user specific databases, use commands ``/save`` and ``/save_mode`` more information in ``/commands``
-  Be able to show custom DB entries with ``/db_list``
-  Add functionality to add alias commands just like a normal command but a string as ``command`` value, which points to
   a ``command_name``. Additionally ``title``, ``description``, ``hidden`` and ``group`` can be set.
-  Autogenerate ResT for all commands with ``/commands rst``, but be aware that double whitespace are not printed. You
   get ``\ \ `` instead, which can be replaced.

Changes
~~~~~~~

-  Bot refactoring:
    -  package ``xenian.bot`` instead of ``xenian_bot``
    -  buildout instead of pipenv
    -  ``bin/bot`` instead of ``run_bot.py``
-  Split utils up and put them in an ``utils`` package
-  Moved the download functions from the reverse search image commands to the utils
-  Combined the reverse search MessageHandlers to one
-  Cleaned up reverse search image command
-  Autodownload ffmpeg if it cannot be found by imageio
-  Improve windows compatibility with file handling
-  Optimized GIF downloader for local file uploader
-  Run GIF downloader asynchronously so users won't get stuck
-  Reply to user message on GIF download, so that the user sees to which GIF the message belongs
-  Improve TTS error message
-  Rename ``tty`` command to ``tts`` (Text-To-Speech) but add an ``tty`` alias for the time being
-  Be able to set a CallbackQueryHandler for a CallbackQuery sender


[1.4.0] - 2018.05.18
--------------------


Added
~~~~~

-  Print raw commands list for the BotFather with ``/commands raw``
-  New filter ``bot_admin``, check if current user is a bot admin
-  ``/random`` - send a random anime gif
-  ``/save_gif`` - *hidden* - save the gif replied to as an anime gif
-  ``/toggle_gif_save`` - *hidden* - toggle auto save sent gifs as anime gif
-  New filter ``anime_save_mode`` to determine if gif save mode is turned on
-  New filters for group permissions: ``bot_group_admin``, ``user_group_admin``, ``reply_user_group_admin``,
   ``all_admin_group``


Changes
~~~~~~~

-  Move dabooru to the **Anime** group
-  Move Video Downloader to the Download group

Fixed
~~~~~

-  Use title for indirect commands instead of command name


[1.3.0] - 2018.05.18
--------------------


Added
~~~~~

-  Mako Template Engine integration


Changes
~~~~~~~

-  Reimplemented the ``/commands`` command with a mako template

Removed
~~~~~~~

-  Temporarily remove the Instagram functionality, better version will come back in the future


[1.2.1] - 2018.02.04
--------------------


Changes
~~~~~~~

-  Fix links to users
-  Fix image to text and translate command name in CHANGELOG and README


[1.2.0] - 2018.02.04
--------------------


Added
~~~~~

-  Group setting for commands
-  Use MongoDB as database, configuration must be set in settings.py
-  Create collection in database with all user, messages and chats
-  ``/itt [-l LANG]`` - Image to Text: Extract text from images
-  ``/itt_lang`` - Languages for ItT: Available languages for Image to Text
-  ``/itt_translate [TEXT] [-lf LANG] [-lt LANG]`` - Image to Text Translation: Extract text from images and translate
   it. ``-lf`` (default: detect, /itt_lang) language on image, to ``-lt`` (default: en, normal language codes) language.


Changes
~~~~~~~

-  Fix command default options
-  Use Filters.all as default for MessageHandler
-  Yandex translate got new function for itself, it is used by the ``/translate`` and ``/itt_translate`` command.


[1.1.2] - 2018-02-04
--------------------


Changes
~~~~~~~

-  Fixed non admin user could use ``/kick``, ``/ban``, ``/warn``
-  Fixed grammatical error in a group management text


[1.1.1] - 2018-02-01
--------------------


Changes
~~~~~~~

-  Add Yandex API Token to settings.example.py


[1.1.0] - 2018-02-01
--------------------


Added
~~~~~

-  ``/tty [TEXT] [-l LANG]`` - Text to speech: Convert text the given text or the message replied to, to text. Use
   ``-l`` to define a language, like de, en or ru
-  ``/translate [TEXT] [-lf LANG] [-lt LANG]`` Translate a reply or a given text from ``-lf`` (default: detect) language
   to ``-lt`` (default: en) language
-  Add utility function ``get_option_from_string`` to extract options from strings sent by a user


Changes
~~~~~~~

-  Update reverse image search wait message if possible
-  Danbooru search only sends finished messages in private chat


[1.0.0] - 2018-01-26
--------------------


Added
~~~~~

-  ``/delete`` has to be a reply to another message to delete this message and warn the user
-  ``/unwarn`` to remove all warnings from a user. Reply with it to a message
-  Add command ``/rules`` to show a groups rules
-  Add command ``/rules`` to show a groups rules
-  Add command ``/rules_define YOUR_RULES`` to define new rules in a group
-  Add command ``/rules_remvoe`` to remove the groups rules
-  Specify a time until user can return from kick with ``/kick [TIME]``
-  Add ``/calc EQUATION`` command to calculate equations inside groups
-  Added ``LOG_LEVEL`` to settings
-  Instagram credentials to the ``settings.py``, which are used for one central Instagram account, instead of
   ``/instali`` and ``/instalo``
-  ``/insta_follow PROFILE_LINK/S OR USERNAME/S`` Instagram Follow: Tell @XenianBot to follow a specific user on
   Instagram, this is used to access private accounts.
-  ``/contribute YOUR_REQUEST`` Send the supporters and admins a request of any kind
-  ``/error ERROR_DESCRIPTION`` If you have found an error please use this command.

Changed
~~~~~~~

-  Run math function asynchronous
-  Disable directly solving equations without command sent to groups
-  Fix not shortening solutions form the calculator
-  Fix message too long for Telegram, for too long solutions from the calculator
-  Remove all ``True`` and ``False`` before trying to calculate so a message with just “true” doesn’t get returned


Removed
~~~~~~~

-  ``/instali``, ``/instalo`` have both been removed in order to have one central defined account
