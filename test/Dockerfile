FROM metabrainz/python:3.7-20210115

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN mkdir /code
WORKDIR /code

# Python dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                       build-essential \
                       git

COPY requirements.txt  /code/requirements.txt
COPY requirements_dev.txt /code/requirements_dev.txt
RUN pip install -r requirements.txt
RUN pip install -r requirements_dev.txt

COPY . /code/

ENV REDIS_HOST "redis"

CMD dockerize -wait tcp://redis:6379 -timeout 10s \
    dockerize -wait tcp://musicbrainz_db:5432 -timeout 10s \
    pytest