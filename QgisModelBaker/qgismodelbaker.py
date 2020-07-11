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
import configparser
import pathlib

from QgisModelBaker.gui.generate_project import GenerateProjectDialog
from QgisModelBaker.gui.export import ExportDialog
from QgisModelBaker.gui.import_data import ImportDataDialog
from QgisModelBaker.libqgsprojectgen.dataobjects.project import Project
from QgisModelBaker.libqgsprojectgen.generator.generator import Generator

from qgis.core import QgsProject
from qgis.utils import available_plugins
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.PyQt.QtCore import QObject, QTranslator, QSettings, QLocale, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon

from QgisModelBaker.gui.options import OptionsDialog
from QgisModelBaker.libili2db.ili2dbconfig import BaseConfiguration

import pyplugin_installer

class QgisModelBakerPlugin(QObject):

    def __init__(self, iface):
        QObject.__init__(self)
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        self.generate_dlg = None
        self.export_dlg = None
        self.importdata_dlg = None

        self.__generate_action = None
        self.__export_action = None
        self.__importdata_action = None
        self.__configure_action = None
        self.__help_action = None
        self.__about_action = None
        self.__separator = None
        basepath = pathlib.Path(__file__).parent.absolute()
        metadata = configparser.ConfigParser()
        metadata.read(os.path.join(basepath, 'metadata.txt'))
        self.__version__ = metadata['general']['version']
        if locale.getlocale() == (None, None):
            locale.setlocale(locale.LC_ALL, '')

        # initialize translation
        qgis_locale_id = str(QSettings().value('locale/userLocale'))
        qgis_locale = QLocale(qgis_locale_id)
        locale_path = os.path.join(self.plugin_dir, 'i18n')
        self.translator = QTranslator()
        self.translator.load(qgis_locale, 'QgisModelBaker', '_', locale_path)
        QCoreApplication.installTranslator(self.translator)

        self.ili2db_configuration = BaseConfiguration()
        settings = QSettings()
        settings.beginGroup('QgisModelBaker/ili2db')
        self.ili2db_configuration.restore(settings)

    def initGui(self):
        pyplugin_installer.installer.initPluginInstaller()
        pyplugin_installer.installer_data.plugins.rebuild()

        if 'projectgenerator' in available_plugins:
            pyplugin_installer.instance().uninstallPlugin('projectgenerator', quiet=True)

        self.__generate_action = QAction( QIcon(os.path.join(os.path.dirname(__file__), 'images/QgisModelBaker-icon.svg')),
            self.tr('Generate'), None)
        self.__export_action = QAction( QIcon(os.path.join(os.path.dirname(__file__), 'images/QgisModelBaker-xtf-export-icon.svg')),
            self.tr('Export Interlis Transfer File (.xtf)'), None)
        self.__importdata_action = QAction( QIcon(os.path.join(os.path.dirname(__file__), 'images/QgisModelBaker-xtf-import-icon.svg')),
            self.tr('Import Interlis Transfer File (.xtf)'), None)
        self.__configure_action = QAction(
            self.tr('Settings'), None)
        self.__help_action = QAction( 
            self.tr('Help'), None)
        self.__about_action = QAction(
            self.tr('About'), None)
        self.__separator = QAction(None)
        self.__separator.setSeparator(True)

        # set these actions checkable to visualize that the dialog is open
        self.__generate_action.setCheckable(True)
        self.__export_action.setCheckable(True)
        self.__importdata_action.setCheckable(True)

        self.__generate_action.triggered.connect(self.show_generate_dialog)
        self.__configure_action.triggered.connect(self.show_options_dialog)
        self.__importdata_action.triggered.connect(self.show_importdata_dialog)
        self.__export_action.triggered.connect(self.show_export_dialog)
        self.__help_action.triggered.connect(self.show_help_documentation)
        self.__about_action.triggered.connect(self.show_about_dialog)

        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__generate_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__importdata_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__export_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__configure_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__separator)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__help_action)
        self.iface.addPluginToDatabaseMenu(
            self.tr('Model Baker'), self.__about_action)

        self.toolbar = self.iface.addToolBar(self.tr('Model Baker'))
        self.toolbar.setObjectName("ModelBakerToolbar")
        self.toolbar.setToolTip(self.tr('Model Baker Toolbar'))
        self.toolbar.addAction(self.__generate_action)
        self.toolbar.addAction(self.__importdata_action)
        self.toolbar.addAction(self.__export_action)

    def unload(self):
        self.iface.removePluginDatabaseMenu(
            self.tr('Model Baker'), self.__generate_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Model Baker'), self.__importdata_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Model Baker'), self.__export_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Model Baker'), self.__configure_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Model Baker'), self.__help_action)
        self.iface.removePluginDatabaseMenu(
            self.tr('Model Baker'), self.__about_action)
        del self.__generate_action
        del self.__export_action
        del self.__importdata_action
        del self.__configure_action
        del self.__help_action
        del self.__about_action

    def show_generate_dialog(self):
        if self.generate_dlg:
            self.generate_dlg.reject()
        else:
            self.generate_dlg = GenerateProjectDialog(self.iface, self.ili2db_configuration, self.iface.mainWindow())
            self.generate_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.generate_dlg.setWindowFlags(self.generate_dlg.windowFlags() | Qt.Tool)
            self.generate_dlg.show()
            self.generate_dlg.finished.connect(self.generate_dialog_finished)
            self.__generate_action.setChecked(True)

    def generate_dialog_finished(self):
        self.__generate_action.setChecked(False)
        self.generate_dlg = None

    def show_export_dialog(self):
        if self.export_dlg:
            self.export_dlg.reject()
        else:
            self.export_dlg = ExportDialog(self.ili2db_configuration, self.iface.mainWindow())
            self.export_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.export_dlg.setWindowFlags(self.export_dlg.windowFlags() | Qt.Tool)
            self.export_dlg.show()
            self.export_dlg.finished.connect(self.export_dialog_finished)
            self.__export_action.setChecked(True)

    def export_dialog_finished(self):
        self.__export_action.setChecked(False)
        self.export_dlg = None

    def show_importdata_dialog(self):
        if self.importdata_dlg:
            self.importdata_dlg.reject()
        else:
            self.importdata_dlg = ImportDataDialog(self.iface, self.ili2db_configuration, self.iface.mainWindow())
            self.importdata_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.importdata_dlg.setWindowFlags(self.importdata_dlg.windowFlags() | Qt.Tool)
            self.importdata_dlg.show()
            self.importdata_dlg.finished.connect(self.importdata_dialog_finished)
            self.__importdata_action.setChecked(True)

    def importdata_dialog_finished(self):
        self.__importdata_action.setChecked(False)
        self.importdata_dlg = None

    def show_options_dialog(self):
        dlg = OptionsDialog(self.ili2db_configuration)
        if dlg.exec_():
            settings = QSettings()
            settings.beginGroup('QgisModelBaker/ili2db')
            self.ili2db_configuration.save(settings)

    def show_help_documentation(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                'https://opengisch.github.io/QgisModelBaker/docs/{}/'.format(os_language))
        else:
            webbrowser.open(
                'https://opengisch.github.io/QgisModelBaker/docs/index.html')

    def show_about_dialog(self):
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setTextFormat(Qt.RichText)
        self.msg.setWindowTitle(self.tr('About Model Baker'))
        self.msg.setText("""<h1>{title}</h1>
        <p align="justify"><small>{version}</small></p>
        <p align="justify">{p1}</p>
        <p align="justify">{p2}</p>
        <p align="justify">{p3}</p>""".format
        (
            title=self.tr('QGIS Model Baker'),
            version=self.tr('Version {version}').format(version=self.__version__),
            p1=self.tr('Configuring QGIS layers and forms manually is a tedious and error prone process. This plugin loads database schemas with various meta information to preconfigure the layer tree, widget configuration, relations and more.'),
            p2=self.tr('This project is open source under the terms of the GPLv2 or later and the source code can be found on <a href="https://github.com/opengisch/QgisModelBaker">github</a>.'),
            p3=self.tr('This plugin is developed by <a href="https://www.opengis.ch/">OPENGIS.ch</a> in collaboration with <a href="https://swisstierrascolombia.com">SwissTierras Colombia</a>')
            ))
        self.msg.setStandardButtons(QMessageBox.Close)
        msg_box = self.msg.exec_()

    def get_generator(self):
        return Generator

    def create_project(self, layers, relations, bags_of_enum, legend, auto_transaction=True, evaluate_default_values=True):
        """
        Expose the main functionality from Model Baker to other plugins,
        namely, create a QGIS project from objects obtained from the Generator
        class.

        :param layers: layers object from generator.layers
        :param relations: relations object obtained from generator.relations
        :param bags_of_enum: bags_of_enum object from generator.relations
        :param legend: legend object obtained from generator.legend
        :param auto_transaction: whether transactions should be enabled or not
                                 when editing layers from supported DB like PG
        :param evaluate_default_values: should default values be evaluated on
                                        provider side when requested and not
                                        when committed. (from QGIS docs)
        """
        project = Project(auto_transaction, evaluate_default_values)
        project.layers = layers
        project.relations = relations
        project.bags_of_enum = bags_of_enum
        project.legend = legend
        project.post_generate()
        qgis_project = QgsProject.instance()
        project.create(None, qgis_project)
