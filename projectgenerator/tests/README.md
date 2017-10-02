# Running the tests

To run the tests inside the same environment as they are executed on Travis,
you need a [Docker](https://www.docker.com/) installation. This will also launch an extra container
with a database, so your own postgres installation is not affected at all.

To run the tests, go to the main directory of the project and do

```sh
export TRAVIS_BUILD_DIR=$PWD # only for local execution
docker-compose -f .docker/docker-compose.travis.yml run qgis /usr/src/.docker/run-docker-tests.sh
```

In one line, removing all containers.
```sh
TRAVIS_BUILD_DIR=$PWD docker-compose -f .docker/docker-compose.travis.yml run qgis /usr/src/.docker/run-docker-tests.sh; TRAVIS_BUILD_DIR=$PWD docker-compose -f .docker/docker-compose.travis.yml rm -s -f
```
