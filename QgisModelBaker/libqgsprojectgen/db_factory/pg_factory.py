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
from ..dbconnector.db_connector import DBConnectorError


class PgFactory(DbFactory):
    """Creates an entire set of objects so that QgisModelBaker supports Postgres/Postgis database.
    """
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
                config_manager = self.get_db_command_config_manager(configuration)
                uri = config_manager.get_uri(True)
                
                _db_connector = self.get_db_connector(uri, configuration.dbschema)

                result = schema_exist = _db_connector.db_or_schema_exists()

                if not schema_exist:
                    _db_connector.create_db_or_schema(configuration.dbusr)
                    result = True

            except (DBConnectorError, FileNotFoundError) as e:
                message = QCoreApplication.translate("PgFactory", "There was an error generating schema with superuser. Check superuser login parameters from settings > General.\n\nReason:\n\n{}").format(str(e))

        return result, message

    def post_generate_project_validations(self, configuration):
        result = False
        message = ''

        config_manager = self.get_db_command_config_manager(configuration)
        uri = config_manager.get_uri(configuration.db_use_super_login)

        connector = self.get_db_connector(uri, configuration.dbschema)

        if not connector._postgis_exists():
            message = QCoreApplication.translate("PgFactory", "The current database does not have PostGIS installed! Please install it by running `CREATE EXTENSION postgis;` on the database before proceeding.")
        else:
            result = True

        return result, message

    def get_tool_version(self, db_ili_version):
        """Returns ili2pg version, regarding to the given version of the used database

        :return: str ili2pg version.
        """
        if db_ili_version == 3:
            return '3.11.2'
        else:
            return '4.4.4'

    def get_tool_url(self, db_ili_version):
        """Returns download url of ili2pg.

        :return str A download url.
        """
        return 'https://downloads.interlis.ch/ili2pg/ili2pg-{version}.zip'.format(version=self.get_tool_version(db_ili_version))
