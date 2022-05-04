FROM python:3.8

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1

RUN apt-get update  && apt-get install -y supervisor libsasl2-dev python-dev libldap2-dev libssl-dev

RUN pip install --upgrade pip

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY . /code/
WORKDIR /code/

COPY /config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8003

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

