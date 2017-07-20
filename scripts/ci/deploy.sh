#!/bin/bash

set -e

PLUGIN_NAME=$(echo $TRAVIS_REPO_SLUG | cut -d'/' -f 2)
METADATA_VERSION=v$(grep -Po "(?<=^version=).*" $PLUGIN_NAME/metadata.txt)

# Check if metadata and tag matches
if [ "$METADATA_VERSION" == "${TRAVIS_TAG}" ];
then
  export RELEASE_VERSION=$METADATA_VERSION
fi
./scripts/ci/update-translations.sh

# Bail out if this is not a release
if [ -z ${RELEASE_VERSION+x} ];
then
  echo -e "\e[31mVersion tag in metadata ($METADATA_VERSION) and in git tag ($TRAVIS_TAG) do not match.\e[0m"
  echo -e "\e[31mThis will not be deployed.\e[0m"
  exit -1
fi

# Tar up all the static files from the git directory
echo -e " \e[33mExporting plugin version ${TRAVIS_TAG} from folder ${PLUGIN_NAME}"
git archive --prefix=${PLUGIN_NAME}/ -o $PLUGIN_NAME-$RELEASE_VERSION.tar HEAD ${PLUGIN_NAME} #${TRAVIS_TAG}:${PLUGIN_NAME}

# Extract to a temporary location
TEMPDIR=/tmp/build-${PLUGIN_NAME}
mkdir -p ${TEMPDIR}/${PLUGIN_NAME}/${PLUGIN_NAME}/i18n
tar -xf ${PLUGIN_NAME}-${RELEASE_VERSION}.tar -C ${TEMPDIR}
mv i18n/*.qm ${TEMPDIR}/${PLUGIN_NAME}/${PLUGIN_NAME}/i18n
DIR=`pwd`
pushd ${TEMPDIR}/${PLUGIN_NAME}
zip -r ${DIR}/${PLUGIN_NAME}-${RELEASE_VERSION}.zip ${PLUGIN_NAME}
popd

echo "## Changes in version $RELEASE_VERSION" > /tmp/changelog 
git log HEAD^...$(git describe --abbrev=0 --tags HEAD^) --pretty=format:"### %s%n%n%b" >> /tmp/changelog

./scripts/ci/plugin_upload.py -u "${OSGEO_USERNAME}" -w "${OSGEO_PASSWORD}" -r "${TRAVIS_TAG}" $PLUGIN_NAME-$RELEASE_VERSION.zip -c /tmp/changelog
