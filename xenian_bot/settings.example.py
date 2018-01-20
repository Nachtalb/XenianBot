TELEGRAM_API_TOKEN = 'YOUR_API_TOKEN'

ADMINS = ['@SOME_TELEGRAM_USERS', ]

# More information about polling and webhooks can be found here:
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks
MODE = {
    'active': 'webhook',  # webook or polling, if webhook further configuration is required
    'webhook': {
        'listen': '127.0.0.1',  # what to listen to, normally localhost
        'port': 5000,  # What port to listen to, if you have multiple bots running they mustn't be the same
        'url_path': TELEGRAM_API_TOKEN,  # Use your API Token so no one can send fake requests
        'url': 'https://your_domain.tld/%s' % TELEGRAM_API_TOKEN,  # Your Public domain, with your token as path so
        # telegram knows where to send the request to
    },
}

UPLOADER = {
    'uploader': 'xenian_bot.uploaders.ssh.SSHUploader',  # What uploader to use
    'url': 'YOUR_DOMAIN_FILES_DIR',
    'configuration': {
        'host': 'YOUR_HOST_IP',
        'user': 'YOUR_USERNAME',
        'password': 'YOUR_PASSWORD',  # If the server does only accepts ssh key login this must be the ssh password
        'upload_dir': 'HOST_UPLOAD_DIRECTORY',
        'key_filename': 'PATH_TO_PUBLIC_SSH_KEY',  # This is not mandatory but some server configurations require it
    }
}
