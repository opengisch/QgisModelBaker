set -e

pushd .docker

docker --version
docker-compose --version
docker-compose -f docker-compose.gh.yml config
docker-compose -f docker-compose.gh.yml build
popd
