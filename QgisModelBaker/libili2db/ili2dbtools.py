# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 07.03.2022
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer / (C) 2021 Germán Carrillo
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

from .globals import DbIliMode


def get_tool_version(tool, db_ili_version):
    if tool == DbIliMode.ili2gpkg:
        if db_ili_version == 3:
            return "3.11.3"
        else:
            return "4.6.1"
    elif tool == DbIliMode.ili2pg:
        if db_ili_version == 3:
            return "3.11.2"
        else:
            return "4.6.1"
    elif tool == DbIliMode.ili2mssql:
        if db_ili_version == 3:
            return "3.12.2"
        else:
            return "4.6.1"

    return "0"


def get_tool_url(tool, db_ili_version):
    if tool == DbIliMode.ili2gpkg:
        return "https://downloads.interlis.ch/ili2gpkg/ili2gpkg-{version}.zip".format(
            version=get_tool_version(tool, db_ili_version)
        )
    elif tool == DbIliMode.ili2pg:
        return "https://downloads.interlis.ch/ili2pg/ili2pg-{version}.zip".format(
            version=get_tool_version(tool, db_ili_version)
        )
    elif tool == DbIliMode.ili2mssql:
        return "https://downloads.interlis.ch/ili2mssql/ili2mssql-{version}.zip".format(
            version=get_tool_version(tool, db_ili_version)
        )

    return ""
