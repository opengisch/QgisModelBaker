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
from QgisModelBaker.libqgsprojectgen.dataobjects import Field


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

    def get_tool_version(self, db_ili_version):
        """Returns ili2gpkg version, regarding to the given version of the used database
        :return: str ili2gpkg version.
        """
        if db_ili_version == 3:
            return '3.12.2'
        else:
            return '4.4.4'

    def get_tool_url(self, db_ili_version):
        """Returns download url of ili2gpkg.

        :return str A download url.
        """
        return 'https://downloads.interlis.ch/ili2mssql/ili2mssql-{version}.zip'.format(version=self.get_tool_version(db_ili_version))

    def customize_widget_editor(self, field: Field, data_type: str):
        if 'bit' in data_type:
            field.widget = 'CheckBox'
            field.widget_config['CheckedState'] = '1'
            field.widget_config['UncheckedState'] = '0'
