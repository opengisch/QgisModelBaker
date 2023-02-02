"""
/***************************************************************************
    begin                :    23/04/19
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
from abc import ABCMeta, abstractmethod
from typing import Tuple

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QWidget

from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType


class AbstractQWidgetMeta(ABCMeta, type(QWidget)):
    pass


class DbConfigPanel(QWidget, metaclass=AbstractQWidgetMeta):
    """Panel where users fill out connection parameters to database. This is a abstract class.

    :ivar bool interlis_mode: Value that determines whether the config panel is displayed with messages or fields interlis.
    :cvar notify_fields_modified: Signal that is called when any field is modified.
    :type notify_field_modified: pyqtSignal(str)
    """

    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent: QWidget, db_action_type: DbActionType):
        """
        :param parent: The parent of this widget.
        :param db_action_type: The action type of QgisModelBaker that will be executed.
        :type db_action_type: :class:`DbActionType`
        """
        QWidget.__init__(self, parent)
        self._db_action_type = db_action_type
        self.interlis_mode = False

    @abstractmethod
    def _show_panel(self):
        """Shows/Hides fields or changes help text before panel is shown."""

    @abstractmethod
    def get_fields(self, configuration: Ili2DbCommandConfiguration):
        """Gets panel fields into `configuration` parameter.

        :param configuration: Object in which the values of the panel fields will be written.
        :type configuration: :class:`Ili2DbCommandConfiguration`
        """

    @abstractmethod
    def set_fields(self, configuration: Ili2DbCommandConfiguration):
        """Set panel fields from `configuration` parameter.

        :param configuration: Object whose instance variables will be written to the fields in the panel
        :type configuration: :class:`Ili2DbCommandConfiguration`
        """

    @abstractmethod
    def is_valid(self) -> Tuple[bool, str]:
        """Checks the config panel has a minimum fields filled out.

        :return: *True* and empty message if the panel has a minimum fields filled out, *False* and warning message otherwise.
        """
