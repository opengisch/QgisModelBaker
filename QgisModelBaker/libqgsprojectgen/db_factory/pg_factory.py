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
from qgis.PyQt.QtCore import QSettings
from .db_factory import DbFactory
from ..dbconnector.pg_connector import PGConnector
from .pg_uri import PgUri
from .pg_layer_uri import PgLayerUri
from ...gui.panel.pg_config_panel import PgConfigPanel
from .ili2pg_args import Ili2pgArgs
from qgis.PyQt.QtCore import QCoreApplication


class PgFactory(DbFactory):

    _settings_base_path = 'QgisModelBaker/ili2pg/'

    def get_db_connector(self, uri, schema):
        return PGConnector(uri, schema)

    def get_config_panel(self, parent, db_action_type):
        return PgConfigPanel(parent, db_action_type)

    def get_db_uri(self):
        return PgUri()

    def get_layer_uri(self, uri):
        return PgLayerUri(uri)

    def get_ili_args(self):
        return Ili2pgArgs()

    def pre_generate_project(self, configuration):
        if configuration.db_use_super_login:
            _db_connector = self.get_db_connector(configuration.super_user_uri, configuration.dbschema)
            if not _db_connector.db_or_schema_exists():
                _db_connector.create_db_or_schema(configuration.dbusr)

    def post_generate_project_validations(self, configuration):
        result = False
        message = ''

        connector = self.get_db_connector(configuration.uri, configuration.dbschema)

        if not connector._postgis_exists():
            message = QCoreApplication.translate("PgFactory", "The current database does not have PostGIS installed! Please install it by running `CREATE EXTENSION postgis;` on the database before proceeding.")
        else:
            result = True

        return result, message

    def save_settings(self, configuration):
        settings = QSettings()
        # PostgreSQL specific options
        settings.setValue(self._settings_base_path + 'host', configuration.dbhost)
        settings.setValue(self._settings_base_path + 'port', configuration.dbport)
        settings.setValue(self._settings_base_path + 'user', configuration.dbusr)
        settings.setValue(self._settings_base_path + 'database', configuration.database)
        settings.setValue(self._settings_base_path + 'schema', configuration.dbschema)
        settings.setValue(self._settings_base_path + 'password', configuration.dbpwd)
        settings.setValue(self._settings_base_path + 'usesuperlogin', configuration.db_use_super_login)

    def load_settings(self, configuration):
        settings = QSettings()

        configuration.dbhost = settings.value(self._settings_base_path + 'host', 'localhost')
        configuration.dbport = settings.value(self._settings_base_path + 'port')
        configuration.dbusr = settings.value(self._settings_base_path + 'user')
        configuration.database = settings.value(self._settings_base_path + 'database')
        configuration.dbschema = settings.value(self._settings_base_path + 'schema')
        configuration.dbpwd = settings.value(self._settings_base_path + 'password')
        configuration.db_use_super_login = settings.value(
            self._settings_base_path + 'usesuperlogin', defaultValue=False, type=bool)

    def get_tool_version(self):
        return '3.11.2'

    def get_tool_url(self):
        return 'http://www.eisenhutinformatik.ch/interlis/ili2pg/ili2pg-{}.zip'.format(self.get_tool_version())
