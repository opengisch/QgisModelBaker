# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    09/05/19
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
from qgis.PyQt.QtCore import QSettings

from .db_command_config_manager import DbCommandConfigManager


class MssqlCommandConfigManager(DbCommandConfigManager):

    _settings_base_path = "QgisModelBaker/ili2mssql/"

    def __init__(self, configuration):
        DbCommandConfigManager.__init__(self, configuration)

    def get_uri(self, su=False):
        separator = ";"
        uri = []
        uri += ["DRIVER={{{}}}".format(self.configuration.db_odbc_driver)]
        host = self.configuration.dbhost
        if self.configuration.dbinstance:
            host += "\\" + self.configuration.dbinstance
        if self.configuration.dbport:
            host += "," + self.configuration.dbport

        uri += ["SERVER={}".format(host)]
        uri += ["DATABASE={}".format(self.configuration.database)]
        uri += ["UID={}".format(self.configuration.dbusr)]
        uri += ["PWD={}".format(self.configuration.dbpwd)]

        return separator.join(uri)

    def get_db_args(self, hide_password=False, su=False):
        db_args = list()
        db_args += ["--dbhost", self.configuration.dbhost]
        if self.configuration.dbport:
            db_args += ["--dbport", self.configuration.dbport]
        db_args += ["--dbusr", self.configuration.dbusr]
        if self.configuration.dbpwd:
            if hide_password:
                db_args += ["--dbpwd", "******"]
            else:
                db_args += ["--dbpwd", self.configuration.dbpwd]
        db_args += ["--dbdatabase", self.configuration.database]
        db_args += [
            "--dbschema",
            self.configuration.dbschema or self.configuration.database,
        ]
        if self.configuration.dbinstance:
            db_args += ["--dbinstance", self.configuration.dbinstance]

        return db_args

    def save_config_in_qsettings(self):
        settings = QSettings()

        settings.setValue(self._settings_base_path + "host", self.configuration.dbhost)
        settings.setValue(
            self._settings_base_path + "instance", self.configuration.dbhost
        )
        settings.setValue(self._settings_base_path + "port", self.configuration.dbport)
        settings.setValue(self._settings_base_path + "user", self.configuration.dbusr)
        settings.setValue(
            self._settings_base_path + "database", self.configuration.database
        )
        settings.setValue(
            self._settings_base_path + "schema", self.configuration.dbschema
        )
        settings.setValue(
            self._settings_base_path + "password", self.configuration.dbpwd
        )
        settings.setValue(
            self._settings_base_path + "odbc_driver", self.configuration.db_odbc_driver
        )

    def load_config_from_qsettings(self):
        settings = QSettings()

        self.configuration.dbhost = settings.value(
            self._settings_base_path + "host", "localhost"
        )
        self.configuration.dbport = settings.value(
            self._settings_base_path + "instance"
        )
        self.configuration.dbport = settings.value(self._settings_base_path + "port")
        self.configuration.dbusr = settings.value(self._settings_base_path + "user")
        self.configuration.database = settings.value(
            self._settings_base_path + "database"
        )
        self.configuration.dbschema = settings.value(
            self._settings_base_path + "schema"
        )
        self.configuration.dbpwd = settings.value(self._settings_base_path + "password")
        self.configuration.db_odbc_driver = settings.value(
            self._settings_base_path + "odbc_driver"
        )
