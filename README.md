# Xenian Bot

[@XenianBot](https://t.me/XenianBot) | [GitHub](https://github.com/Nachtalb/XenianBot)

<!-- toc -->

- [What I do](#what-i-do)
- [Commands](#commands)
- [Contributions](#contributions)
  * [Bug report / Feature request](#bug-report--feature-request)
  * [Code Contribution / Pull Requests](#code-contribution--pull-requests)
  * [Development](#development)
    + [Command Concept](#command-concept)

<!-- tocstop -->

## What I do
I am a personal assistant which can do various tasks for you. For example, I can do reverse image searches directly here
in Telegram. To see my full capability, send me /commands and you will see everything available or go to
[Commands](#commands).

## Commands
- `/start` Start using me
- `/commands` Get a list of commands, for all the things I can do for you.
- `/define TEXT` Use this to search for a word or some words on Urban Dictionary.
- `/insta POST_LINK OR POST_ID` Send me a link to an Instagram post or its ID and I will send you the image/s or video 
  from that post.
- `/instap USER_LINK OR USERNAME` Send me a username or the link to a user from Instagram and I will send you all its 
  posts.
- `/instli USERNAME PASSWORD` To be able to use the Instagram service, you first need to be logged in. You can do this 
  with this simple command. DO NOT USE THIS COMMAND IN GROUPS. 
- `/instlo` Logout from Instagram. 
Use this command at your own risk, because with active users you may get a ton of images and videos. 
- `/rawl` Rawl numbers from 0 to 10000 so you can get your sexy dubs, trips and quads.
- More will come soon if you have any ideas or stuff you want: [Contribuions](#contributions)


- Reverse Image / Video / Gif / Sticker Search available. Just send one of the said files and the search starts 
  automatically.
## Contributions
### Bug report / Feature request
If you have found a bug or want a new feature, please file an issue on GitHub [Issues](https://github.com/Nachtalb/python_telegram_bot_template/issues)

### Code Contribution / Pull Requests
Please use a line length of 120 characters and [Google Style Python Docstrings](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html). 

### Development
Instead of the old `pip` with `requirements.txt`, I use the new and fancy [pipenv](https://github.com/pypa/pipfile), 
which works with [pipfile](https://docs.pipenv.org). You can get more information by following the links. If you read 
the pipenv documentation you will also be able to understand by yourself why I use, it instead of me talking about it here. 

With this info we now install our virtualenv with: 
```bash
pip install pipenv      # Install pipenv
pipenv install --three  # Create virtualeenv from your python3 installation and install the packages from the Pipfile
pipenv shell            # Spawn shell for your pipenv virtualenv
``` 

After this is complete, you have to get an API Token from Telegram. You can easily get one via the
[@BotFather](https://t.me/BotFather).

Now that you have your API Token, copy the `settings.example.py` to `settings.py` and paste in your API Token. Configure 
the rest of the settings.py and you are ready to go. Start the bot 
```bash
python run_bot.py
```

#### Command Concept
I am still working on how I want to make the commends to be used as easily as possible. At the moment this is how it 
works:

In the folder `python_telegram_bot_template/commands/` you'll find a `__init__.py`, `base.py` and `builtins.py`.
The `base.py` contains the base command, which is used for every other command. It has the following attributes:
- `all_commands`: This is a variable containing all the commands which you create with this class as Parent. If you 
override the `__init__` method you have to call super init otherwise, the command will not be added to this list. This 
list is used for adding the commands as handlers for telegram and for creating the commands list.
- `command_name`: This is what the user has to run So for the start command it would be `start`. If you do not define 
one yourself, the lowercase string of the name of your class is taken.
- `title` This is the title of your command. This does not have to be the same as the `command_name`. Your 
`command_name` could be eg. `desc` so the command would be `/desc`, but the title would be `Describe`. Like this, it is 
easier for the user to get the meaning of function from a command directly from the command list.
- `description`: As the name says, this is the description. It is shown on the command list. Describe what your command 
does in a few words.
- `handler`: This is the handler your command uses. This could be `MessageHandler`. `CommandHandler` or any other 
handler. By default, the `CommandHandler` is used. 
- `options`: This is a dict of arguments given to the handler. For the `CommandHandler`, these would be at least 
`command` and `callback`. These are given by default via the `__init__` method. The `command` is the `command_name` and 
the `callback` the `command` method.
- `hidden`: If the command is hidden from the command list. By default this is False.
- `args`: If you have args, you can write them here. Eg. a command like this: `/add_human Nick 20 male` your text would 
be like `NAME AGE GENDER`. This will be shown on the command list. 

Now we get to the methods. 
- `__init__`: Initializes the command. It adds the command to the `command_all` list, as well as sets the default for 
the `command_name` and `title` if it has to. It also sets the default `options`. If you override this function in one of 
your commands, do not forget to super init it. Otherwise, it will not be initialized and not added to the command list.
- `command`: The actual command function for your operation. This has at least the two arguments `bot` and `update`
which come from the `python-telegram-bot`. In here you define the actual logic of your code. If you do not implement 
this method in your command, you will get a `NotImplementedError`.

After you create your command, you have to call it at least once. It doesn't matter where you call it from, but I like 
to just call it directly after the class as you can see in the builtins.py. And do not forget that the file with the 
command must be loaded imported somewhere. I usually do this directly in the `__init__.py`.

#### Uploaders Concept
Like for the commands I tried to make it easier to use different kinds of file storage. You can find a configuration in 
the settings.py and the "uploaders" itself in the `python_telegram_bot_template/uploaaders/` folder. The goal is that
you can only change the configuration in the settings.py and your bot works without any further adjustment. So you could
use the local file system for local development and then switch to ssh for production, or something like this. 

You get the uploader by `from python_telegram_bot_template.uploaders import uploader`. If you use it you should always
start with `uploader.connect()` then upload / save whatever you want with `uploader.upload(...)` and finally close the 
connection with `uploader.close()`. You should even use this if you are using the file system. It is to prevent errors 
when you switch it someday in the future. 

Now to the attributes and so on: 
- `_mandatory_configuration`: It defines what must be in the configuration inside the settings.py.
E.g. for the file system this is
```python
{'path': str}
``` 
which means you have to define
```python
UPLOADER = {
    'uploader': 'xenian_bot.uploaders.file_system.FileSystemUploader',  # What uploader to use
    'configuration': {
        'path': '/some/path/to/your/uploads',
    }
}
```
If you are using the ssh uploader you have to define more:
```python
{'host': str, 'user': str, 'password': str, 'upload_dir': str}
```
```python
UPLOADER = {
    'uploader': 'xenian_bot.uploaders.ssh.SSHUploader',
    'configuration': {
        'host': '000.000.000.000',
        'user': 'chuck.norris',
        'password': 'i_am_immortal',
        'upload_dir': '/some/path/on/your/server/',
        'key_filename': '/home/chuck.norris/.ssh/id_rsa',  # This is not defined as mandatory because on most ssh 
        # servers you don't only use the ssh key as authentication, but if you do define this configuration as well.
    }
}
```
As you can see in the dict's above it is always a name as key and a type as value. This is checked when you initialize 
the uploader the first time.
- `configuration`: Filled in on the initialization from the uploader. It contains the configuration defined in the 
settings.py


Now to the methods: 
- `__init__`: As always this initializes the uploader. If you need to override it, don't forget to call super init 
otherwise, the configuration is not checked and applied.
- `connect`: Connect to the server / service or whatever. This method doesn't need to be implemented. E.g. the file 
system didn't need it. 
- `close`: Close the connection to the server / service ... This method too doesn't have to be implemented.
- `uplaod`: In here you define the actual logic of the uploader. If you do not implement this method in your custom 
uploader there will be an `NotImplementedError` raised, when used.

Thank you for using [@XenianBot](https://t.me/XenianBot).
