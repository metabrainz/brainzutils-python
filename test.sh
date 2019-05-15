#!/bin/bash

docker-compose -f test/docker-compose.py2.yml up --build
docker-compose -f test/docker-compose.py3.yml up --build
