#!/bin/bash

cd $(dirname $0)/..
export GITHUB_WORKSPACE=$PWD
docker-compose -f .docker/docker-compose.gh.yml run qgis /usr/src/.docker/run-docker-tests.sh $@
docker-compose -f .docker/docker-compose.gh.yml rm -s -f
