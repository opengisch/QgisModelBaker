#!/usr/bin/env bash
#***************************************************************************
#                             -------------------
#       begin                : 2017-08-24
#       git sha              : :%H$
#       copyright            : (C) 2017 by OPENGIS.ch
#       email                : info@opengis.ch
#***************************************************************************
#
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#***************************************************************************

set -e

/usr/src/QgisModelBaker/tests/testdata/mssql/setup-mssql.sh


# rationale: Wait for postgres container to become available
echo "Wait a moment while loading the database."
while ! PGPASSWORD='docker' psql -h postgres -U docker -p 5432 -l &> /dev/null
do
  printf "."
  sleep 2
done
echo ""


pushd /usr/src
xvfb-run nose2-3
popd
