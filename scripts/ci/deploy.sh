#!/bin/bash

set -e

PLUGIN_NAME=$(echo $TRAVIS_REPO_SLUG | cut -d'/' -f 2)
METADATA_VERSION=v$(grep -Po "(?<=^version=).*" $PLUGIN_NAME/metadata.txt)
if [ "$METADATA_VERSION" != "${TRAVIS_TAG}" ]; then
  echo -e "\e[31mVersion tag in metadata ($METADATA_VERSION) and in git tag ($TRAVIS_TAG) do not match.\e[0m"
  echo -e "\e[31mThis will not be deployed.\e[0m"
  exit -1
fi

echo -e " \e[33mExporting plugin version ${TRAVIS_TAG} from folder ${PLUGIN_NAME}"
git archive --prefix=${PLUGIN_NAME}/ -o $PLUGIN_NAME-$METADATA_VERSION.zip HEAD projectgenerator #${TRAVIS_TAG}:${PLUGIN_NAME}


mkdir -p /tmp/projectgenerator/i18n
mv i18n/*.qm /tmp/projectgenerator/i18n
DIR=`pwd`
pushd /tmp
zip -ur $DIR/$PLUGIN_NAME-$METADATA_VERSION.zip projectgenerator
popd

echo "## Changes in version $METADATA_VERSION" > /tmp/changelog 
git log HEAD^...$(git describe --abbrev=0 --tags HEAD^) --pretty=format:"### %s%n%n%b" >> /tmp/changelog

./scripts/ci/plugin_upload.py -u "${OSGEO_USERNAME}" -w "${OSGEO_PASSWORD}" -r "${TRAVIS_TAG}" $PLUGIN_NAME-$METADATA_VERSION.zip -c /tmp/changelog
