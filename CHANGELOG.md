# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Added

- `/tty [TEXT] [-l LANG]` - Text to speech: Convert text the given text or the message replied to, to text. Use `-l` to define a language, like de, en or ru
- `/translate [TEXT] [-lf LANG] [-lt LANG]` Translate a reply or a given text from `-lf` (default: detect) language to `-lt` (default: en) language
- Add utility function `get_option_from_string` to extract options from strings sent by a user

### Changes
- Update reverse image search wait message if possible
- Danbooru search only sends finished messages in private chat

## [1.0.0] - 2018-01-26

### Added

- `/delete` has to be a reply to another message to delete this message and warn the user
- `/unwarn` to remove all warnings from a user. Reply with it to a message
- Add command `/rules` to show a groups rules
- Add command `/rules` to show a groups rules
- Add command `/rules_define YOUR_RULES` to define new rules in a group
- Add command `/rules_remvoe` to remove the groups rules
- Specify a time until user can return from kick with `/kick [TIME]`
- Add `/calc EQUATION` command to calculate equations inside groups
- Added `LOG_LEVEL` to settings
- Instagram credentials to the `settings.py`, which are used for one central Instagram account, instead of `/instali` and `/instalo`
- `/insta_follow PROFILE_LINK/S OR USERNAME/S` Instagram Follow: Tell @XenianBot to follow a specific user on Instagram, this is used to access private accounts.
- `/contribute YOUR_REQUEST` Send the supporters and admins a request of any kind
- `/error ERROR_DESCRIPTION` If you have found an error please use this command.

### Changed
- Run math function asynchronous
- Disable directly solving equations without command sent to groups
- Fix not shortening solutions form the calculator
- Fix message too long for Telegram, for too long solutions from the calculator
- Remove all `True` and `False` before trying to calculate so a message with just "true" doesn't get returned

### Removed

- `/instali`, `/instalo` have both been removed in order to have one central defined account
