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
    """Manages a configuration object to return specific information of some database. This is a abstract class.

    Provides database uri, arguments to ili2db and a way to save and load configurations parameters
    based on a object configuration.

    :ivar configuration object that will be managed
    """

    def __init__(self, configuration: Ili2DbCommandConfiguration):
        """
        :param configuration: Configuration object that will be managed.
        :type configuration: :class:`Ili2DbCommandConfiguration`
        """
        self.configuration = configuration

    @abstractmethod
    def get_uri(self, su: bool = False):
        """Gets database uri (connection string) for db connectors (:class:`DBConnector`).

        :param bool su: *True* to use super user credentials, *False* otherwise.
        :return: Database uri (connection string).
        :rtype str
        """
        pass

    @abstractmethod
    def get_db_args(self, hide_password=False, su=False):
        """Gets a list of ili2db arguments related to database.

        :param bool hide_password: *True* to mask the password, *False* otherwise.
        :param bool su: *True* to use super user password, *False* otherwise. Default is False.
        :return: ili2db arguments list.
        :rtype: list
        """
        pass

    def get_schema_import_args(self):
        """Gets a list of ili2db arguments to use in operation schema import.

        :return: ili2db arguments list.
        :rtype: list
        """
        return list()

    def get_ili2db_args(self, hide_password=False):
        """Gets a complete list of ili2db arguments in order to execute the app.

        :param bool hide_password: *True* to mask the password, *False* otherwise.
        :return: ili2db arguments list.
        :rtype: list
        """
        db_args = self.get_db_args(hide_password, self.configuration.db_use_super_login)

        if type(self.configuration) is SchemaImportConfiguration:
            db_args += self.get_schema_import_args()

        ili2dbargs = self.configuration.to_ili2db_args(db_args)

        return ili2dbargs

    @abstractmethod
    def save_config_in_qsettings(self):
        """Saves configuration values related to database in QSettings.

        :return: None
        """
        pass

    @abstractmethod
    def load_config_from_qsettings(self):
        """Loads configuration values related to database from Qsettings.

        :return: None
        """
        pass
