Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/en/1.0.0/>`__ and this project adheres to `Semantic
Versioning <http://semver.org/spec/v2.0.0.html>`__.

[1.5.0] - Unreleased
--------------------

Added
~~~~~

-  Custom user specific databases, use commands ``/save`` and ``/save_mode`` more information in ``/commands``

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
