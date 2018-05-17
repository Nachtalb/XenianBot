import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TELEGRAM_API_TOKEN = 'YOUR_API_TOKEN'
YANDEX_API_TOKEN = 'YOUR_YANDEX_API_TOKEN'

ADMINS = ['@SOME_TELEGRAM_USERS', ]  # Users which can do admin tasks like /restart
SUPPORTER = ['@SOME_TELEGRAM_USERS', ]  # Users which to contact fo support

TEMPLATE_DIR = os.path.join(BASE_DIR, 'xenian_bot/commands/templates')

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

LOG_LEVEL = logging.INFO

# These Instagram credentials are used for the centralized Instagram account which automatically follows private
# accounts and downloads images / videos
INSTAGRAM_CREDENTIALS = {
    'username': 'INSTAGRAM_USERNAME',
    'password': 'INSTAGRAM_PASSWORD',
}

MONGODB_CONFIGURATION = {
    'host': 'HOST_OF_YOUR_DB',  # default: localhost
    'port': 'PORT_OF_YOUR_DB_AS_INT',  # default: 27017
    'db_name': 'DATABASE_NAME',
}

IMAGE_TO_TEXT_LANG = [  # All languages available for tesseract: https://github.com/tesseract-ocr/tessdata_best
    ('afr', 'Afrikaans'), ('amh', 'Amharic'), ('ara', 'Arabic'), ('asm', 'Assamese'), ('aze', 'Azerbaijani'),
    ('aze_cyrl', 'Azerbaijani - Cyrillic'), ('bel', 'Belarusian'), ('ben', 'Bengali'), ('bod', 'Tibetan'),
    ('bos', 'Bosnian'), ('bul', 'Bulgarian'), ('cat', 'Catalan; Valencian'), ('ceb', 'Cebuano'), ('ces', 'Czech'),
    ('chi_sim', 'Chinese - Simplified'), ('chi_tra', 'Chinese - Traditional'), ('chr', 'Cherokee'), ('cym', 'Welsh'),
    ('dan', 'Danish'), ('deu', 'German'), ('dzo', 'Dzongkha'), ('ell', 'Greek, Modern (1453-)'), ('eng', 'English'),
    ('enm', 'English, Middle (1100-1500)'), ('epo', 'Esperanto'), ('est', 'Estonian'), ('eus', 'Basque'),
    ('fas', 'Persian'), ('fin', 'Finnish'), ('fra', 'French'), ('frk', 'Frankish'),
    ('frm', 'French, Middle (ca. 1400-1600)'), ('gle', 'Irish'), ('glg', 'Galician'), ('grc', 'Greek, Ancient (-1453)'),
    ('guj', 'Gujarati'), ('hat', 'Haitian; Haitian Creole'), ('heb', 'Hebrew'), ('hin', 'Hindi'), ('hrv', 'Croatian'),
    ('hun', 'Hungarian'), ('iku', 'Inuktitut'), ('ind', 'Indonesian'), ('isl', 'Icelandic'), ('ita', 'Italian'),
    ('ita_old', 'Italian - Old'), ('jav', 'Javanese'), ('jpn', 'Japanese'), ('kan', 'Kannada'), ('kat', 'Georgian'),
    ('kat_old', 'Georgian - Old'), ('kaz', 'Kazakh'), ('khm', 'Central Khmer'), ('kir', 'Kirghiz; Kyrgyz'),
    ('kor', 'Korean'), ('kur', 'Kurdish'), ('lao', 'Lao'), ('lat', 'Latin'), ('lav', 'Latvian'), ('lit', 'Lithuanian'),
    ('mal', 'Malayalam'), ('mar', 'Marathi'), ('mkd', 'Macedonian'), ('mlt', 'Maltese'), ('msa', 'Malay'),
    ('mya', 'Burmese'), ('nep', 'Nepali'), ('nld', 'Dutch; Flemish'), ('nor', 'Norwegian'), ('ori', 'Oriya'),
    ('pan', 'Panjabi; Punjabi'), ('pol', 'Polish'), ('por', 'Portuguese'), ('pus', 'Pushto; Pashto'),
    ('ron', 'Romanian; Moldavian; Moldovan'), ('rus', 'Russian'), ('san', 'Sanskrit'), ('sin', 'Sinhala; Sinhalese'),
    ('slk', 'Slovak'), ('slv', 'Slovenian'), ('spa', 'Spanish; Castilian'), ('spa_old', 'Spanish; Castilian - Old'),
    ('sqi', 'Albanian'), ('srp', 'Serbian'), ('srp_latn', 'Serbian - Latin'), ('swa', 'Swahili'), ('swe', 'Swedish'),
    ('syr', 'Syriac'), ('tam', 'Tamil'), ('tel', 'Telugu'), ('tgk', 'Tajik'), ('tgl', 'Tagalog'), ('tha', 'Thai'),
    ('tir', 'Tigrinya'), ('tur', 'Turkish'), ('uig', 'Uighur; Uyghur'), ('ukr', 'Ukrainian'), ('urd', 'Urdu'),
    ('uzb', 'Uzbek'), ('uzb_cyrl', 'Uzbek - Cyrillic'), ('vie', 'Vietnamese'), ('yid', 'Yiddish')
]
