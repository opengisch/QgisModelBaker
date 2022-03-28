# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    18/06/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania (BSF Swissphoto)
    email                :    yesidpol.3@gmail.com
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
import re

import pyodbc

from QgisModelBaker.gui.panel.db_config_panel import DbActionType, DbConfigPanel
from QgisModelBaker.gui.panel.gpkg_config_panel import GpkgConfigPanel
from QgisModelBaker.gui.panel.mssql_config_panel import MssqlConfigPanel
from QgisModelBaker.gui.panel.pg_config_panel import PgConfigPanel
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode

regex_list = ["sql.*server", "mssql", "FreeTDS"]


def get_odbc_drivers():
    result = list()
    for item in pyodbc.drivers():
        regex_sql_server = "({})".format("|".join(regex_list))

        x = re.search(regex_sql_server, item, re.IGNORECASE)

        if x:
            result.append(item)

    return result


# Get panel depending on DB
def get_config_panel(self, tool, parent, db_action_type: DbActionType) -> DbConfigPanel:
    """Returns an instance of a panel where users to fill out connection parameters to database.
    :param parent: The parent of this widget.
    :param db_action_type: The action type of QgisModelBaker that will be executed.
    :type db_action_type: :class:`DbActionType`
    :return: A panel where users to fill out connection parameters to database.
    :rtype: :class:`DbConfigPanel`
    """
    if tool == DbIliMode.ili2gpkg:
        return GpkgConfigPanel(parent, db_action_type)
    elif tool == DbIliMode.ili2pg:
        return PgConfigPanel(parent, db_action_type)
    elif tool == DbIliMode.ili2mssql:
        return MssqlConfigPanel(parent, db_action_type)

    return DbConfigPanel(parent, db_action_type)
