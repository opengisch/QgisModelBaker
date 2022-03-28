#!/bin/bash
LIBS_DIR="QgisModelBaker/libs"
PGSERVICEPARSER=("pgserviceparser" "1.0.1")
PACKAGING=("packaging" "21.3")
PYODBC=("pyodbc" "4.0.32")

PACKAGES=(
  PGSERVICEPARSER[@]
  PACKAGING[@]
  PYODBC[@]
)

#create lib folder
mkdir -p $LIBS_DIR

for PACKAGE in ${PACKAGES[@]}; do
  echo download and unpack ${!PACKAGE:0:1} with version ${!PACKAGE:1:1}
  #create temp folder
  mkdir -p temp
  #download the wheel
  pip download -v ${!PACKAGE:0:1}==${!PACKAGE:1:1} --only-binary :all: -d temp/
  #unpack the wheel
  unzip -o temp/${!PACKAGE:0:1}*.whl -d $LIBS_DIR
  #remove temp folder
  rm -r temp
done
