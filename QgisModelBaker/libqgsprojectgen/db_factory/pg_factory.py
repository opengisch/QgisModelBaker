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
from ...gui.panel.pg_config_panel import PgConfigPanel


class PgFactory(DbFactory):

    def get_db_connector(self, uri, schema):
        return PGConnector(uri, schema)

    def get_config_panel(self, parent):
        return PgConfigPanel(parent)

    def save_settings(self, configuration):
        # TODO repair string path settings
        settings = QSettings()
        # PostgreSQL specific options
        settings.setValue(
            'QgisModelBaker/ili2pg/host', configuration.dbhost)
        settings.setValue(
            'QgisModelBaker/ili2pg/port', configuration.dbport)
        settings.setValue(
            'QgisModelBaker/ili2pg/user', configuration.dbusr)
        settings.setValue(
            'QgisModelBaker/ili2pg/database', configuration.database.strip("'"))
        settings.setValue(
            'QgisModelBaker/ili2pg/schema', configuration.dbschema)
        settings.setValue(
            'QgisModelBaker/ili2pg/password', configuration.dbpwd)
        settings.setValue(
            'QgisModelBaker/ili2pg/usesuperlogin', configuration.db_use_super_login)

    def load_settings(self, configuration):
        settings = QSettings()

        configuration.dbhost = settings.value('QgisModelBaker/ili2pg/host', 'localhost')
        configuration.dbport = settings.value('QgisModelBaker/ili2pg/port')
        configuration.dbusr = settings.value('QgisModelBaker/ili2pg/user')
        configuration.database = settings.value('QgisModelBaker/ili2pg/database')
        configuration.dbschema = settings.value('QgisModelBaker/ili2pg/schema')
        configuration.dbpwd = settings.value('QgisModelBaker/ili2pg/password')
        configuration.db_use_super_login = settings.value('QgisModelBaker/ili2pg/usesuperlogin', defaultValue=False, type=bool)

