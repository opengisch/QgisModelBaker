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
import locale

from PyQt5.QtCore import QSettings

from projectgenerator.gui.generate_project import GenerateProjectDialog
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.PyQt.QtCore import QObject

from projectgenerator.gui.options import OptionsDialog
from projectgenerator.libili2pg.ili2pg_config import BaseConfiguration


class QgsProjectGeneratorPlugin(QObject):
    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        self.__generate_action = None
        self.__configure_action = None
        if locale.getlocale() == (None, None):
            locale.setlocale(locale.LC_ALL, '')

        self.ili2db_configuration = BaseConfiguration()
        settings = QSettings()
        settings.beginGroup('QgsProjectGenerator/ili2db')
        self.ili2db_configuration.restore(settings)

    def initGui(self):
        self.__generate_action = QAction(self.tr('Generate'), None)
        self.__configure_action = QAction(self.tr('Settings'), None)

        self.__generate_action.triggered.connect(self.show_generate_dialog)
        self.__configure_action.triggered.connect(self.show_options_dialog)

        self.iface.addPluginToDatabaseMenu(self.tr('Project Generator'), self.__generate_action)
        self.iface.addPluginToDatabaseMenu(self.tr('Project Generator'), self.__configure_action)

    def unload(self):
        self.iface.removePluginDatabaseMenu(self.tr('Project Generator'), self.__generate_action)
        self.iface.removePluginDatabaseMenu(self.tr('Project Generator'), self.__configure_action)
        del self.__generate_action

    def show_generate_dialog(self):
        dlg = GenerateProjectDialog(self.ili2db_configuration)
        dlg.exec_()

    def show_options_dialog(self):
        dlg = OptionsDialog(self.ili2db_configuration)
        if dlg.exec_():
            settings = QSettings()
            settings.beginGroup('QgsProjectGenerator/ili2db')
            self.ili2db_configuration.save(settings)
