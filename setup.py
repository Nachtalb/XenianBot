from setuptools import find_packages
from setuptools import setup

version = '2.5.2'


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
          'emoji',
          'googletrans',
          'gtts',
          'htmlmin',
          'mako',
          'moviepy',
          'mr.developer',
          'paramiko',
          'pillow',
          'pybooru',
          'pymongo',
          'pytesseract',
          'python-telegram-bot',
          'requests',
          'requests-html',
          'setuptools',
          'urbandictionary',
          'youtube-dl',
      ],

      entry_points={
          'console_scripts': [
              'bot = xenian.bot.bot:main']
      })
