FROM python:3.11-slim-bullseye

LABEL maintainer="Nachtalb"

ENV PYTHONIOENCODING=utf-8


RUN \
 apt update && \
 apt install -yq \
   ffmpeg

WORKDIR /bot
COPY requirements.txt /bot/requirements.txt

RUN \
  pip install -U --no-cache-dir pip setuptools && \
  pip install --no-cache-dir -r requirements.txt

RUN \
 apt clean -y && \
 rm -rf \
   /var/lib/apt/lists/* \
   /var/tmp/*

COPY . /bot

RUN groupadd -g 1000 python && \
   useradd -u 1000 -g python python && \
   chown -R python:python /bot

USER python:python

ENTRYPOINT ["python", "-m", "xenian.bot.cli"]
