#!/bin/bash
LIBS_DIR="QgisModelBaker/libs"

MODELBAKER_LIBRARY=("modelbaker" "2.0.0")
PACKAGING=("packaging" "21.3")

PACKAGES=(
  MODELBAKER_LIBRARY[@]
  PACKAGING[@]
)

#create lib folder
mkdir -p $LIBS_DIR

for PACKAGE in ${PACKAGES[@]}; do
  echo download and unpack ${!PACKAGE:0:1} with version ${!PACKAGE:1:1}
  #create temp folder
  mkdir -p temp
  #download the wheel
  pip download -v ${!PACKAGE:0:1}==${!PACKAGE:1:1} --only-binary :all: -d temp/
  #unpack all the wheels found (means including dependencies)
  unzip -o "temp/*.whl" -d $LIBS_DIR
  #remove temp folder
  rm -r temp
  #set write rights to group (because qgis-plugin-ci needs it)
  chmod -R a+rwx $LIBS_DIR
done

#create the __init__.py in libs folder
cd $LIBS_DIR
touch __init__.py
chmod a+rwx __init__.py
