#!/bin/bash

docker-compose -f test/docker-compose.yml -p brainzutils_test run --rm test "$@"
