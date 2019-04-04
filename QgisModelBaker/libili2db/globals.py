# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 3.10.2017
        git sha              : :%H$
        copyright            : (C) 2017 by Matthias Kuhn
        email                : matthias@opengis.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from enum import IntFlag

CRS_PATTERNS = {
    'LV95': 2056,
    'LV03': 21781
}

class DbIliMode(IntFlag):
    pg = 1
    gpkg = 2
    mssql = 4

    ili = 1024

    ili2pg = ili | pg
    ili2gpkg = ili | gpkg
    ili2mssql = ili | mssql

displayDbIliMode = {
    DbIliMode.pg: "PostgreSQL/PostGIS",
    DbIliMode.gpkg: "GeoPackage",
    DbIliMode.mssql: "SQL Server",
    DbIliMode.ili: "Interlis",
    DbIliMode.ili2pg: "ili2pg",
    DbIliMode.ili2gpkg: "ili2gpkg",
    DbIliMode.ili2mssql: "ili2mssql"
}
