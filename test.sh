#!/bin/bash

#!/bin/bash

# Github Actions automatically sets the CI environment variable. We use this variable to detect if the script is running
# inside a CI environment and modify its execution as needed.
if [ "$CI" == "true" ] ; then
    echo "Running in CI mode"
fi

# UNIT TESTS
# ./test.sh                build unit test containers, bring up, make database, test, bring down
# for development:
# ./test.sh -u             build unit test containers, bring up background and load database if needed
# ./test.sh [params]       run unit tests, passing optional params to inner test
# ./test.sh -s             stop unit test containers without removing
# ./test.sh -d             clean unit test containers

COMPOSE_FILE_LOC=test/docker-compose.yml
COMPOSE_PROJECT_NAME=brainzutils_test

echo "Checking docker compose version"
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

function invoke_docker_compose {
    $DOCKER_COMPOSE_CMD \
      -f $COMPOSE_FILE_LOC \
      -p $COMPOSE_PROJECT_NAME \
      "$@"
}

function docker_compose_run {
    invoke_docker_compose run --rm --user `id -u`:`id -g` "$@"
}

function build_unit_containers {
    invoke_docker_compose build 
}

function bring_up_unit_db {
    invoke_docker_compose up -d redis musicbrainz_db
}

function is_unit_db_running {
    # Check if the database container is running
    containername="${COMPOSE_PROJECT_NAME}_musicbrainz_db_1"
    res=`docker ps --filter "name=$containername" --filter "status=running" -q`
    if [ -n "$res" ]; then
        return 0
    else
        return 1
    fi
}

function is_unit_db_exists {
    containername="${COMPOSE_PROJECT_NAME}_musicbrainz_db_1"
    res=`docker ps --filter "name=$containername" --filter "status=exited" -q`
    if [ -n "$res" ]; then
        return 0
    else
        return 1
    fi
}

# Exit immediately if a command exits with a non-zero status.
# set -e
# trap cleanup EXIT  # Cleanup after tests finish running


if [ "$1" == "-s" ]; then
    echo "Stopping unit test containers"
    invoke_docker_compose stop
    exit 0
fi

if [ "$1" == "-d" ]; then
    echo "Running docker-compose down"
    invoke_docker_compose down
    exit 0
fi

# if -u flag, bring up db, run setup, quit
if [ "$1" == "-u" ]; then
    is_unit_db_exists
    DB_EXISTS=$?
    is_unit_db_running
    DB_RUNNING=$?
    if [ $DB_EXISTS -eq 0 -o $DB_RUNNING -eq 0 ]; then
        echo "Database is already up, doing nothing"
    else
        echo "Building containers"
        invoke_docker_compose build
        echo "Bringing up DB"
        bring_up_unit_db
    fi
    exit 0
fi

is_unit_db_exists
DB_EXISTS=$?
is_unit_db_running
DB_RUNNING=$?
if [ $DB_EXISTS -eq 1 -a $DB_RUNNING -eq 1 ]; then
    # If no containers, build them, run setup then run tests, then bring down
    invoke_docker_compose build
    bring_up_unit_db
    echo "Running tests"
    docker_compose_run test "$@"
    RET=$?
    invoke_docker_compose down
    exit $RET
else
    # Else, we have containers, just run tests
    echo "Running tests"
    docker_compose_run test "$@"
    exit $?
fi
