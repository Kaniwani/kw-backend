FROM python:3.6

RUN apt-get update

RUN mkdir -p /app
WORKDIR /app

ADD ./requirements.txt /app
ADD ./requirements-dev.txt /app
RUN pip install -r /app/requirements.txt
RUN pip install -r /app/requirements-dev.txt

EXPOSE 8000
