# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    13/05/19
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

from .db_command_config_manager import DbCommandConfigManager


class GpkgCommandConfigManager(DbCommandConfigManager):
    """Manages a configuration object to return specific information of Geopackage.

    Provides database uri, arguments to ili2db and a way to save and load configurations parameters
    based on a object configuration.

    :ivar configuration object that will be managed
    """

    _settings_base_path = "QgisModelBaker/ili2gpkg/"

    def __init__(self, configuration):
        DbCommandConfigManager.__init__(self, configuration)

    def get_uri(self, su=False):
        return self.configuration.dbfile

    def get_db_args(self, hide_password=False, su=False):
        return ["--dbfile", self.configuration.dbfile]

    def save_config_in_qsettings(self):
        settings = QSettings()
        settings.setValue(
            self._settings_base_path + "dbfile", self.configuration.dbfile
        )

    def load_config_from_qsettings(self):
        settings = QSettings()
        self.configuration.dbfile = settings.value(self._settings_base_path + "dbfile")
