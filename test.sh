#!/bin/bash

docker-compose -f test/docker-compose.yml -p brainzutils_test run --rm test "$@"
RET=$?
docker-compose -f test/docker-compose.yml -p brainzutils_test down
exit $RET
