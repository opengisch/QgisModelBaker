#!/bin/bash

# Arguments are passed one to one to pytest
#
# Run all tests:
# ./scripts/run-tests.sh # Run all tests
#
# Run all test starting with test_array_
# ./scripts/run-tests.sh -k test_array_

if [ -z "$QGIS_TEST_VERSION" ]; then
  export QGIS_TEST_VERSION=latest # See https://hub.docker.com/r/qgis/qgis/tags/
fi

cd $(dirname $0)/..
export GITHUB_WORKSPACE=$PWD # only for local execution

docker-compose -f .docker/docker-compose.gh.yml run qgis /usr/src/.docker/run-docker-tests.sh $@
docker-compose -f .docker/docker-compose.gh.yml rm -s -f
