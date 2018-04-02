#!/bin/bash

MY_PATH="`dirname \"$0\"`"              # relative
MY_PATH="`( cd \"$MY_PATH\" && pwd )`"  # absolutized and normalized

cd "$MY_PATH"/..

export TRAVIS_BUILD_DIR=$PWD
docker-compose -f .docker/docker-compose.travis.yml run qgis /usr/src/.docker/run-docker-tests.sh
docker-compose -f .docker/docker-compose.travis.yml rm -s -f
