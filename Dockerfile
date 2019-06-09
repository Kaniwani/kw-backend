FROM python:3.6

RUN apt-get update

RUN mkdir -p /app
WORKDIR /app

ADD ./requirements.txt /app
RUN pip install -r /app/requirements.txt
ADD ./wanikani_api-0.2.0-py36-none-any.whl /app
RUN pip install wanikani_api-0.2.0-py36-none-any.whl

EXPOSE 8000
