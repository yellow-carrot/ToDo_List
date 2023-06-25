FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONNUNBUFFERED 1

RUN pip install --upgrade pip

ADD requirements.txt /usr/src/app/requirements.txt

RUN pip install -r /usr/src/app/requirements.txt

COPY . /usr/src/app

WORKDIR /usr/src/app/todolist

COPY . /usr/src/app/todolist

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]