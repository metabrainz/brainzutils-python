FROM metabrainz/python:3.6-20210115 as brainzutils-pytest

ENV DOCKERIZE_VERSION v0.2.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Python dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                       build-essential \
                       git

RUN mkdir /code
RUN mkdir /data
WORKDIR /code

COPY requirements.txt  /code/requirements.txt
COPY requirements_dev.txt /code/requirements_dev.txt
RUN pip install -r requirements.txt
RUN pip install -r requirements_dev.txt

COPY . /code/

ENV REDIS_HOST "redis"

CMD dockerize -wait tcp://redis:6379 -timeout 10s \
    py.test --junitxml=/data/test_report-py3.xml \
            --cov-report xml:/data/coverage.xml


FROM brainzutils-pytest as brainzutils-pylint

CMD find . -iname "*.py" | xargs pylint -j 4 | tee /data/pylint.out