# type: ignore
from setuptools import find_packages
from setuptools import setup

version = "2.5.3.dev0"


setup(
    name="XenianBot",
    version=version,
    description="Multifunctional Telegram Bot",
    long_description=f'{open("README.rst").read()}\n{open("CHANGELOG.rst").read()}',
    author="Nachtalb",
    url="https://github.com/Nachtalb/XenianBot",
    license="GPL3",
    packages=find_packages(exclude=["ez_setup"]),
    namespace_packages=["xenian"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "emoji==2.2.0",
        "googletrans==4.0.0rc1",
        "gTTS==2.1.1",
        "htmlmin==0.1.12",
        "Mako==1.1.3",
        "moviepy==1.0.3",
        "paramiko==2.7.1",
        "Pillow==9.4.0",
        "Pybooru==4.2.0",
        "pymongo==3.11.0",
        "pytesseract==0.3.10",
        "python-telegram-bot==12.8",
        "requests-html==0.10.0",
        "urbandictionary==1.1",
        "yt-dlp==2023.1.6",
        "decorator==4.4.2",
        "idna<3a",
        "python-dotenv==0.21.1",
    ],
    entry_points={"console_scripts": ["bot = xenian.bot.bot:main"]},
)
