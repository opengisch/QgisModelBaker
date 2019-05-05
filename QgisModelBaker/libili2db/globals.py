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
from enum import IntFlag, Enum
from qgis.PyQt.QtCore import QCoreApplication


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
    DbIliMode.pg: QCoreApplication.translate('QgisModelBaker', 'PostgreSQL/PostGIS'),
    DbIliMode.gpkg: QCoreApplication.translate('QgisModelBaker', 'GeoPackage'),
    DbIliMode.mssql: QCoreApplication.translate('QgisModelBaker', 'SQL Server'),
    DbIliMode.ili: QCoreApplication.translate('QgisModelBaker', 'Interlis'),
    DbIliMode.ili2pg: QCoreApplication.translate('QgisModelBaker', 'Interlis (use PostGIS)'),
    DbIliMode.ili2gpkg: QCoreApplication.translate('QgisModelBaker', 'Interlis (use GeoPackage)'),
    DbIliMode.ili2mssql: QCoreApplication.translate('QgisModelBaker', 'Interlis (use SQL Server)')
}


class DbActionType(Enum):
    GENERATE = 1
    IMPORT_DATA = 2
    EXPORT = 3

