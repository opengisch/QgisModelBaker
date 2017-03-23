# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2017-01-27
        git sha              : :%H$
        copyright            : (C) 2017 by OPENGIS.ch
        email                : info@opengis.ch
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
from .gui.generate_project import GenerateProjectDialog
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.PyQt.QtCore import QObject


class QgsProjectGeneratorPlugin(QObject):
    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        self.__generate_action = None
        self.__configure_action = None

    def initGui(self):
        menu = QMenu()
        self.__generate_action = QAction(self.tr('Generate'))
        self.__configure_action = QAction(self.tr('Settings'))

        self.__generate_action.triggered.connect(self.show_generate_dialog)

        self.iface.addPluginToDatabaseMenu(self.tr('Project Generator'), self.__generate_action)

    def unload(self):
        self.iface.removePluginDatabaseMenu(self.tr('Project Generator'), self.__generate_action)
        del self.__generate_action

    def show_generate_dialog(self):
        dlg = GenerateProjectDialog()
        dlg.exec_()

    def show_settings_dialog(self):
        pass
