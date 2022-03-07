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
from abc import ABC, abstractmethod
from typing import Tuple

from QgisModelBaker.gui.panel.db_config_panel import DbConfigPanel
from QgisModelBaker.libili2db.globals import DbActionType
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration
from QgisModelBaker.libqgsprojectgen.dataobjects.fields import Field

from ..dbconnector.db_connector import DBConnector
from .db_command_config_manager import DbCommandConfigManager
from .layer_uri import LayerUri


class DbFactory(ABC):
    """Creates an entire set of objects so that QgisModelBaker supports some database. This is a abstract class."""

    @abstractmethod
    def get_db_connector(self, uri: str, schema: str) -> DBConnector:
        """Returns an instance of connector to database (:class:`DBConnector`).

        :param str uri: Database connection string.
        :param str schema: Database schema.
        :return: A connector to specific database.
        :rtype: :class:`DBConnector`
        :raises :class:`DBConnectorError`: when the connection fails.
        """

    @abstractmethod
    def get_config_panel(self, parent, db_action_type: DbActionType) -> DbConfigPanel:
        """Returns an instance of a panel where users to fill out connection parameters to database.

        :param parent: The parent of this widget.
        :param db_action_type: The action type of QgisModelBaker that will be executed.
        :type db_action_type: :class:`DbActionType`
        :return: A panel where users to fill out connection parameters to database.
        :rtype: :class:`DbConfigPanel`
        """

    @abstractmethod
    def get_db_command_config_manager(
        self, configuration: Ili2DbCommandConfiguration
    ) -> DbCommandConfigManager:
        """Returns an instance of a database command config manager.

        :param configuration: Configuration object that will be managed.
        :type configuration: :class:`Ili2DbCommandConfiguration`
        :return: Object that manages a configuration object to return specific information of some database.
        :rtype :class:`DbCommandConfigManager`
        """

    @abstractmethod
    def get_layer_uri(self, uri: str) -> LayerUri:
        """Returns an instance of a layer uri.

        :param str uri: Database connection string.
        :return: A object that provides layer uri.
        :rtype :class:`LayerUri`
        """

    @abstractmethod
    def pre_generate_project(
        self, configuration: Ili2DbCommandConfiguration
    ) -> Tuple[bool, str]:
        """This method will be called before an operation of generate project is executed.

        :param configuration: Configuration parameters with which will be executed the operation of generate project.
        :type configuration: :class:`Ili2DbCommandConfiguration`
        :return: *True* and an empty message if the called method was succeeded, *False* and a warning message otherwise.
        """

    @abstractmethod
    def post_generate_project_validations(
        self, configuration: Ili2DbCommandConfiguration
    ) -> Tuple[bool, str]:
        """This method will be called after an operation of generate project is executed.

        :param configuration: Configuration parameters with which were executed the operation of generate project.
        :type configuration: :class:`Ili2DbCommandConfiguration`
        :return: *True* and an empty message if the called method was succeeded, *False* and a warning message otherwise.
        """

    def get_specific_messages(self):
        """Returns specific words that will be use in warning and error messages.

        :rtype dict
        """
        messages = {"db_or_schema": "schema", "layers_source": "schema"}

        return messages

    def customize_widget_editor(self, field: Field, data_type: str):
        """Allows customizing the way a field is shown in the widget editor.

        For instance, a boolean field can be shown as a checkbox.

        :param field: The field that will be customized
        :type field: :class:`Field`
        :param data_type: The type of field
        :return None
        """
