# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    08/04/19
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
from ..dbconnector.pg_connector import PGConnector
from .pg_layer_uri import PgLayerUri
from QgisModelBaker.gui.panel.pg_config_panel import PgConfigPanel
from .pg_command_config_manager import PgCommandConfigManager
from qgis.PyQt.QtCore import QCoreApplication
from psycopg2 import OperationalError


class PgFactory(DbFactory):

    def get_db_connector(self, uri, schema):
        return PGConnector(uri, schema)

    def get_config_panel(self, parent, db_action_type):
        return PgConfigPanel(parent, db_action_type)

    def get_db_command_config_manager(self, configuration):
        return PgCommandConfigManager(configuration)

    def get_layer_uri(self, uri):
        return PgLayerUri(uri)

    def pre_generate_project(self, configuration):
        result = not configuration.db_use_super_login
        message = ''

        if configuration.db_use_super_login:
            try:
                _db_connector = self.get_db_connector(configuration.super_user_uri, configuration.dbschema)

                result = schema_exist = _db_connector.db_or_schema_exists()

                if not schema_exist:
                    _db_connector.create_db_or_schema(configuration.dbusr)
                    result = True

            except OperationalError:
                message = QCoreApplication.translate("PgFactory", "There was an error generating schema with superuser. Check superuser login parameters from settings > General.")

        return result, message

    def post_generate_project_validations(self, configuration):
        result = False
        message = ''

        connector = self.get_db_connector(configuration.uri, configuration.dbschema)

        if not connector._postgis_exists():
            message = QCoreApplication.translate("PgFactory", "The current database does not have PostGIS installed! Please install it by running `CREATE EXTENSION postgis;` on the database before proceeding.")
        else:
            result = True

        return result, message

    def get_tool_version(self):
        return '3.11.2'

    def get_tool_url(self):
        return 'http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-{}.zip'.format(self.get_tool_version())

    def get_schema_import_args(self):
        args = list()
        args += ["--setupPgExt"]
        return args