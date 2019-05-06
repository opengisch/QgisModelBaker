# -*- coding: utf-8 -*-
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
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QWidget
from abc import ABC, abstractmethod


class DbConfigPanel(QWidget):

    notify_fields_modified = pyqtSignal(str)

    def __init__(self, parent, db_action_type):
        QWidget.__init__(self, parent)
        self._db_action_type = db_action_type
        self.interlis_mode = False

    @abstractmethod
    def _show_panel(self):
        pass

    @abstractmethod
    def get_fields(self, configuration):
        """
        Get Panel fields into 'configuration' parameter
        :param configuration: (Ili2DbCommandConfiguration)
        """
        pass

    @abstractmethod
    def set_fields(self, configuration):
        """
        Set Panel fields
        :param configuration: (Ili2DbCommandConfiguration)
        """
        pass

    @abstractmethod
    def is_valid(self):
        pass

    def showEvent(self, event):
        self._show_panel()
