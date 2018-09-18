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
import os
import webbrowser

from projectgenerator.gui.generate_project import GenerateProjectDialog
from projectgenerator.gui.export import ExportDialog
from projectgenerator.gui.import_data import ImportDataDialog
from projectgenerator.libqgsprojectgen.dataobjects.project import Project
from projectgenerator.libqgsprojectgen.generator.generator import Generator

from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.PyQt.QtCore import QObject, QTranslator, QSettings, QLocale, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon

from projectgenerator.gui.options import OptionsDialog
from projectgenerator.libili2db.ili2dbconfig import BaseConfiguration

class QgsProjectGeneratorPlugin(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.__generate_action = None
        self.__export_action = None
        self.__importdata_action = None
        self.__configure_action = None
        self.__help_action = None
        self.__about_action = None
        self.__separator = None
        if locale.getlocale() == (None, None):
            locale.setlocale(locale.LC_ALL, '')

        # initialize translation
        qgis_locale = QLocale(QSettings().value('locale/userLocale'))
        locale_path = os.path.join(self.plugin_dir, 'i18n')
        self.translator = QTranslator()
        self.translator.load(qgis_locale, 'projectgenerator', '_', locale_path)
        QCoreApplication.installTranslator(self.translator)

        self.ili2db_configuration = BaseConfiguration()
        settings = QSettings()
        settings.beginGroup('QgsProjectGenerator/ili2db')
        self.ili2db_configuration.restore(settings)

    def initGui(self):
        self.__generate_action = QAction( QIcon(os.path.join(os.path.dirname(__file__), 'images/projectgenerator-icon.svg')),
            self.tr('Generate'), None)
        self.__export_action = QAction( QIcon(os.path.join(os.path.dirname(__file__), 'images/projectgenerator-xtf-export-icon.svg')),
            self.tr('Export Interlis Transfer File (.xtf)'), None)
        self.__importdata_action = QAction( QIcon(os.path.join(os.path.dirname(__file__), 'images/projectgenerator-xtf-import-icon.svg')),
            self.tr('Import Interlis Transfer File (.xtf)'), None)
        self.__configure_action = QAction(
            self.tr('Settings'), None)
        self.__help_action = QAction( 
            self.tr('Help'), None)
        self.__about_action = QAction(
            self.tr('About'), None)
        self.__separator = QAction(None)
        self.__separator.setSeparator(True)

        self.__generate_action.triggered.connect(self.show_generate_dialog)
        self.__configure_action.triggered.connect(self.show_options_dialog)
        self.__importdata_action.triggered.connect(self.show_importdata_dialog)
        self.__export_action.triggered.connect(self.show_export_dialog)
        self.__help_action.triggered.connect(self.show_help_documentation)
        self.__about_action.triggered.connect(self.show_about_dialog)

        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__generate_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__importdata_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__export_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__configure_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__separator)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__help_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Project Generator'), self.__about_action)

        self.toolbar = self.iface.addToolBar(self.tr('Project Generator'))
        self.toolbar.setObjectName("ProjectGeneratorToolbar")
        self.toolbar.setToolTip(self.tr('Project Generator Toolbar'))
        self.toolbar.addAction(self.__generate_action)
        self.toolbar.addAction(self.__importdata_action)
        self.toolbar.addAction(self.__export_action)

    def unload(self):
        self.iface.removePluginDatabaseMenu(
            self.tr('Project Generator'), self.__generate_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Project Generator'), self.__importdata_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Project Generator'), self.__export_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Project Generator'), self.__configure_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Project Generator'), self.__help_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Project Generator'), self.__about_action)
        del self.__generate_action
        del self.__export_action
        del self.__importdata_action
        del self.__configure_action
        del self.__help_action
        del self.__about_action

    def show_generate_dialog(self):
        dlg = GenerateProjectDialog(self.iface, self.ili2db_configuration)
        dlg.exec_()

    def show_options_dialog(self):
        dlg = OptionsDialog(self.ili2db_configuration)
        if dlg.exec_():
            settings = QSettings()
            settings.beginGroup('QgsProjectGenerator/ili2db')
            self.ili2db_configuration.save(settings)

    def show_export_dialog(self):
        dlg = ExportDialog(self.ili2db_configuration)
        dlg.exec_()

    def show_importdata_dialog(self):
        dlg = ImportDataDialog(self.ili2db_configuration)
        dlg.exec_()

    def show_help_documentation(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                'https://opengisch.github.io/projectgenerator/docs/{}/'.format(os_language))
        else:
            webbrowser.open(
                'https://opengisch.github.io/projectgenerator/docs/index.html')

    def show_about_dialog(self):
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setTextFormat(Qt.RichText)
        self.msg.setWindowTitle(self.tr('About Project Generator'))
        self.msg.setText(self.tr(
            """<h1>Project Generator</h1>
        <p align="justify">Configuring QGIS layers and forms manually is a tedious and error prone process. This plugin loads database schemas with various meta
        information to preconfigure the layer tree, widget configuration, relations and more.</p>
        <p align="justify">This project is open source under the terms of the GPLv2 or later and the source code can be found on <a href="https://github.com/opengisch/projectgenerator">github</a>.</p>
        <p align="justify">This plugin is developed by <a href="https://www.opengis.ch/">OPENGIS.ch</a> in collaboration with
        <a href="https://www.proadmintierra.info/">Agencia de Implementación (BSF-Swissphoto AG / INCIGE S.A.S.)</a>.</p></p>"""))
        self.msg.setStandardButtons(QMessageBox.Close)
        msg_box = self.msg.exec_()

    def get_generator(self):
        return Generator

    def create_project(self, layers, relations, legend, auto_transaction=True, evaluate_default_values=True):
        project = Project(auto_transaction, evaluate_default_values)
        project.layers = layers
        project.relations = relations
        project.legend = legend
        project.post_generate()
        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)
