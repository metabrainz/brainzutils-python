#!/usr/bin/env bash
set -xe

# Modify these two as needed:
COMPOSE_FILE_LOC="test/docker-compose.test.yml"

# BUILD_TAG
# String of jenkins-${JOB_NAME}-${BUILD_NUMBER}
# https://www.jenkins.io/doc/book/pipeline/jenkinsfile/
COMPOSE_PROJECT_NAME_ORIGINAL="${BUILD_TAG}"

# Project name is sanitized by Compose, so we need to do the same thing.
# See https://github.com/docker/compose/issues/2119.
COMPOSE_PROJECT_NAME=$(echo $COMPOSE_PROJECT_NAME_ORIGINAL | awk '{print tolower($0)}' | sed 's/[^a-z0-9]*//g')
TEST_CONTAINER_REF="_${TEST_CONTAINER_NAME}_1"

# Record installed version of Docker and Compose with each build
echo "Docker environment:"
docker --version
docker-compose --version

function cleanup {
    # Shutting down all containers associated with this project
    docker-compose -f $COMPOSE_FILE_LOC \
                   -p $COMPOSE_PROJECT_NAME \
                   down --remove-orphans
    #docker ps -a --no-trunc  | grep $COMPOSE_PROJECT_NAME \
    #    | awk '{print $1}' | xargs -r --no-run-if-empty docker stop
    #docker ps -a --no-trunc  | grep $COMPOSE_PROJECT_NAME \
    #    | awk '{print $1}' | xargs -r --no-run-if-empty docker rm
}

function run_tests {
    # Create containers
    docker-compose -f $COMPOSE_FILE_LOC \
                   -p $COMPOSE_PROJECT_NAME \
                   build

    # List images and containers related to this build
    docker images | grep $COMPOSE_PROJECT_NAME | awk '{print $0}'
    docker ps -a | grep $COMPOSE_PROJECT_NAME | awk '{print $0}'

    docker-compose -f $COMPOSE_FILE_LOC -p $COMPOSE_PROJECT_NAME run --name ${COMPOSE_PROJECT_NAME}_run_py2 \
            test_py2 || true
    docker-compose -f $COMPOSE_FILE_LOC -p $COMPOSE_PROJECT_NAME run --name ${COMPOSE_PROJECT_NAME}_run_py3 \
            test_py3 || true
    docker-compose -f $COMPOSE_FILE_LOC -p $COMPOSE_PROJECT_NAME run --name ${COMPOSE_PROJECT_NAME}_run_pylint \
            test_pylint || true
}

function  extract_results {
    docker cp ${COMPOSE_PROJECT_NAME}_run_pylint:/data/pylint.out . || true
    docker cp ${COMPOSE_PROJECT_NAME}_run_py2:/data/test_report2.xml . || true
    docker cp ${COMPOSE_PROJECT_NAME}_run_py3:/data/test_report3.xml . || true
    docker cp ${COMPOSE_PROJECT_NAME}_run_py3:/data/coverage.xml . || true
}

set -e
cleanup            # Initial cleanup
trap cleanup EXIT  # Cleanup after tests finish running

run_tests
extract_results
