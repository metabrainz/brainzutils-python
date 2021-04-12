#!/bin/bash

docker-compose -f test/docker-compose.test.yml -p brainzutils_test run --rm test
