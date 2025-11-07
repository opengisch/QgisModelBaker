"""
/***************************************************************************
                              -------------------
        begin                : 16.12.2021
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
        email                : david at opengis ch
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

from enum import Enum

from qgis.PyQt.QtCore import QCoreApplication

from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType

CRS_PATTERNS = {"LV95": 2056, "LV03": 21781}

DEFAULT_DATASETNAME = "Baseset"
CATALOGUE_DATASETNAME = "Catalogueset"

displayDbIliMode = {
    DbIliMode.pg: QCoreApplication.translate("QgisModelBaker", "PostGIS"),
    DbIliMode.gpkg: QCoreApplication.translate("QgisModelBaker", "GeoPackage"),
    DbIliMode.mssql: QCoreApplication.translate("QgisModelBaker", "SQL Server"),
    DbIliMode.ili: QCoreApplication.translate("QgisModelBaker", "INTERLIS"),
    DbIliMode.ili2pg: QCoreApplication.translate(
        "QgisModelBaker", "INTERLIS (use PostGIS)"
    ),
    DbIliMode.ili2gpkg: QCoreApplication.translate(
        "QgisModelBaker", "INTERLIS (use GeoPackage)"
    ),
    DbIliMode.ili2mssql: QCoreApplication.translate(
        "QgisModelBaker", "INTERLIS (use SQL Server)"
    ),
}

displayLanguages = {
    "en": QCoreApplication.translate("QgisModelBaker", "English"),
    "de": QCoreApplication.translate("QgisModelBaker", "German"),
    "fr": QCoreApplication.translate("QgisModelBaker", "French"),
    "it": QCoreApplication.translate("QgisModelBaker", "Italian"),
    "rm": QCoreApplication.translate("QgisModelBaker", "Romansh"),
}


class AdministrativeDBActionTypes(Enum):
    """Defines constants for modelbaker actions that require superuser login"""

    SCHEMA_IMPORT = DbActionType.SCHEMA_IMPORT
    IMPORT_DATA = DbActionType.IMPORT_DATA
