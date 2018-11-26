from setuptools import find_packages
from setuptools import setup

version = '2.0.2'


setup(name='XenianBot',
      version=version,
      description="Multifunctional Telegram Bot",
      long_description=f'{open("README.rst").read()}\n{open("CHANGELOG.rst").read()}',

      author='Nachtalb',
      url='https://github.com/Nachtalb/XenianBot',
      license='GPL3',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['xenian'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
          'python-telegram-bot',
          'paramiko',
          'urbandictionary',
          'emoji',
          'requests',
          'moviepy',
          'pybooru',
          'youtube-dl',
          'gtts',
          'yandex.translate',
          'pymongo',
          'pytesseract',
          'pillow',
          'mako',
          'htmlmin',
          'setuptools',
      ],

      entry_points={
          'console_scripts': [
              'bot = xenian.bot.bot:main']
      })
