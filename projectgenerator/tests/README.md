# Running the tests

To run the tests inside the same environment as they are executed on Travis,
you need a [Docker](https://www.docker.com/) installation. This will also launch an extra container
with a database, so your own postgres installation is not affected at all.

To run the tests, go to the main directory of the project and do

```sh
# only for local execution
export TRAVIS_BUILD_DIR=$PWD
# run and destroy container
docker-compose -f .docker/docker-compose.travis.yml run --rm qgis /usr/src/.docker/run-docker-tests.sh
```

In one line, removing all containers, for clean execution.
```sh
export TRAVIS_BUILD_DIR=$PWD && docker-compose -f .docker/docker-compose.travis.yml rm -s -f && docker-compose -f .docker/docker-compose.travis.yml run --rm qgis /usr/src/.docker/run-docker-tests.sh
```

If you use sudo.
```sh
sudo TRAVIS_BUILD_DIR=$PWD docker-compose -f .docker/docker-compose.travis.yml rm -s -f && sudo TRAVIS_BUILD_DIR=$PWD docker-compose -f .docker/docker-compose.travis.yml run --rm qgis /usr/src/.docker/run-docker-tests.sh
```
