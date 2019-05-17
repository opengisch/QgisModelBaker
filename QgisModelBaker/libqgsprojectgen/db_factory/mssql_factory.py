# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    10/05/19
    git sha              :    :%H$
    copyright            :    (C) 2019 by Yesid Polania
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
from .db_factory import DbFactory
from ..dbconnector.mssql_connector import MssqlConnector
from .mssql_command_config_manager import MssqlCommandConfigManager
from .mssql_layer_uri import MssqlLayerUri
from QgisModelBaker.gui.panel.mssql_config_panel import MssqlConfigPanel


class MssqlFactory(DbFactory):

    def get_db_connector(self, uri, schema):
        return MssqlConnector(uri, schema)

    def get_config_panel(self, parent, db_action_type):
        return MssqlConfigPanel(parent, db_action_type)

    def get_db_command_config_manager(self, configuration):
        return MssqlCommandConfigManager(configuration)

    def get_layer_uri(self, uri):
        return MssqlLayerUri(uri)

    def pre_generate_project(self, configuration):
        return True, ''

    def post_generate_project_validations(self, configuration):
        return True, ''

    def get_tool_version(self):
        return '3.12.2'

    def get_tool_url(self):
        return 'https://github.com/AgenciaImplementacion/ili2db/releases/download/ili2mssql-{}/ili2mssql.zip'.format(self.get_tool_version())
