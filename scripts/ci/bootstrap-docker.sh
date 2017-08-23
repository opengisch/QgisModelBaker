set -e

pushd .docker

docker --version
docker-compose --version
docker-compose -f docker-compose.travis.yml config
docker-compose -f docker-compose.travis.yml build
popd
