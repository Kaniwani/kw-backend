FROM python:3

EXPOSE 8000

RUN mkdir /app
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD python manage.py runserver
