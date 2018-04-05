#!/bin/bash

cd $(dirname $0)/..
export TRAVIS_BUILD_DIR=$PWD
docker-compose -f .docker/docker-compose.travis.yml run qgis /usr/src/.docker/run-docker-tests.sh
docker-compose -f .docker/docker-compose.travis.yml rm -s -f
