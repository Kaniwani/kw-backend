FROM python:3.6

RUN apt-get update

RUN mkdir -p /app
WORKDIR /app

ADD ./requirements.txt /app
RUN pip install -r /app/requirements.txt

EXPOSE 8000
