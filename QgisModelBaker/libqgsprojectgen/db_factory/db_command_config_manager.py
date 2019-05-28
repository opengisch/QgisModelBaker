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
from abc import ABC, abstractmethod
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration, SchemaImportConfiguration


class DbCommandConfigManager(ABC):

    def __init__(self, configuration: Ili2DbCommandConfiguration):
        self.configuration = configuration

    @abstractmethod
    def get_uri(self, su: bool):
        pass

    @abstractmethod
    def get_db_args(self, hide_password=False):
        pass

    def get_schema_import_args(self):
        return list()

    def get_ili2db_args(self, hide_password=False):
        db_args = self.get_db_args(hide_password)

        if type(self.configuration) is SchemaImportConfiguration:
            db_args += self.get_schema_import_args()

        ili2dbargs = self.configuration.to_ili2db_args(db_args)

        return ili2dbargs

    @abstractmethod
    def save_config_in_qsettings(self):
        pass

    @abstractmethod
    def load_config_from_qsettings(self):
        pass
