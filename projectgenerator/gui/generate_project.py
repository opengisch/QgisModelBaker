# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 29/03/17
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

import os

from projectgenerator.gui.config import ConfigDialog
from projectgenerator.gui.ili2pg_options import Ili2pgOptionsDialog
from projectgenerator.libili2pg.iliimporter import JavaNotFoundError
from projectgenerator.utils.qt_utils import make_file_selector
from qgis.PyQt.QtGui import QColor, QDesktopServices, QFont
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt.QtCore import QCoreApplication, QSettings
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from qgis.gui import QgsProjectionSelectionDialog
from ..utils import get_ui_class
from ..libili2pg import iliimporter
from ..libqgsprojectgen.generator.postgres import Generator
from ..libqgsprojectgen.dataobjects import Project

DIALOG_UI = get_ui_class('generate_project.ui')


class GenerateProjectDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.addButton(self.tr('Create'), QDialogButtonBox.AcceptRole)
        self.ili_file_browse_button.clicked.connect(make_file_selector(self.ili_file_line_edit, title=self.tr('Open Interlis Model'), file_filter=self.tr('Interlis Model File (*.ili)')))
        self.crs = QgsCoordinateReferenceSystem()
        self.ili2pg_options = Ili2pgOptionsDialog()
        self.ili2pg_options_button.clicked.connect(self.ili2pg_options.open)
        self.type_combo_box.clear()
        self.type_combo_box.addItem(self.tr('Interlis'), 'ili')
        self.type_combo_box.addItem(self.tr('Postgis'), 'pg')
        self.type_combo_box.currentIndexChanged.connect(self.type_changed)
        self.txtStdout.anchorClicked.connect(self.link_activated)
        self.crsSelector.crsChanged.connect(self.crs_changed)

        self.text = ''

        self.restore_configuration()

    def accepted(self):
        configuration = self.updated_configuration()

        if self.type_combo_box.currentData() == 'ili':
            importer = iliimporter.Importer()

            importer.configuration = configuration

            self.save_configuration(configuration)

            importer.stdout.connect(self.print_info)
            importer.stderr.connect(self.on_stderr)
            importer.process_started.connect(self.on_process_started)
            importer.process_finished.connect(self.on_process_finished)

            try:
                if importer.run() != iliimporter.Importer.SUCCESS:
                    return
            except JavaNotFoundError:
                self.txtStdout.setTextColor(QColor('#000000'))
                self.txtStdout.clear()
                self.txtStdout.setText(self.tr('Java could not be found. Please <a href="https://java.com/en/download/">install Java</a> and or <a href="#configure">configure a custom java path</a>. We also support the JAVA_HOME environment variable in case you prefer this.'))
                return

            configuration.schema = configuration.schema or configuration.database

        generator = Generator(configuration.uri, configuration.schema)
        available_layers = generator.layers()
        relations = generator.relations(available_layers)
        legend = generator.legend(available_layers)

        project = Project()
        project.layers = available_layers
        project.relations = relations
        project.legend = legend

        qgis_project = QgsProject.instance()
        project.layer_added.connect(self.print_info)
        project.create(None, qgis_project)

    def print_info(self, text):
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        self.txtStdout.setTextColor(QColor('#aa2222'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        self.txtStdout.setTextColor(QColor('#777777'))
        self.txtStdout.append('Finished ({})'.format(exit_code))
        if result == iliimporter.Importer.SUCCESS:
            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
        else:
            self.enable()

    def updated_configuration(self):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = iliimporter.Configuration()

        configuration.host = self.pg_host_line_edit.text()
        configuration.user = self.pg_user_line_edit.text()
        configuration.database = self.pg_database_line_edit.text()
        configuration.schema = self.pg_schema_line_edit.text()
        configuration.password = self.pg_password_line_edit.text()
        configuration.ilifile = self.ili_file_line_edit.text()
        configuration.epsg = self.epsg
        configuration.inheritance = self.ili2pg_options.get_inheritance_type()
        configuration.java_path = QSettings().value('QgsProjectGenerator/java_path', '')

        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgsProjectGenerator/ili2pg/ilifile', configuration.ilifile)
        settings.setValue('QgsProjectGenerator/ili2pg/epsg', self.epsg)
        settings.setValue('QgsProjectGenerator/ili2pg/host', configuration.host)
        settings.setValue('QgsProjectGenerator/ili2pg/user', configuration.user)
        settings.setValue('QgsProjectGenerator/ili2pg/database', configuration.database)
        settings.setValue('QgsProjectGenerator/ili2pg/schema', configuration.schema)
        settings.setValue('QgsProjectGenerator/ili2pg/password', configuration.password)
        settings.setValue('QgsProjectGenerator/importtype', self.type_combo_box.currentData())

    def restore_configuration(self):
        settings = QSettings()

        self.ili_file_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/ilifile'))
        self.crs = QgsCoordinateReferenceSystem(settings.value('QgsProjectGenerator/ili2pg/epsg', 21781))
        self.update_crs_info()
        self.pg_host_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/host', 'localhost'))
        self.pg_user_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/user'))
        self.pg_database_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/database'))
        self.pg_schema_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/schema'))
        self.pg_password_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/password'))
        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(settings.value('QgsProjectGenerator/importtype', 'pg')))
        self.type_changed()
        self.crs_changed()

    def disable(self):
        self.pg_config.setEnabled(False)
        self.ili_config.setEnabled(False)
        self.buttonBox.setEnabled(False)

    def enable(self):
        self.pg_config.setEnabled(True)
        self.ili_config.setEnabled(True)
        self.buttonBox.setEnabled(True)

    def type_changed(self):
        if self.type_combo_box.currentData() == 'ili':
            self.ili_config.show()
        else:
            self.ili_config.hide()

    def link_activated(self, link):
        if link.url() == '#configure':
            configuraton = self.updated_configuration()
            cfg = ConfigDialog(configuraton)
            if cfg.exec_():
                # That's quite ugly
                QSettings().setValue('QgsProjectGenerator/java_path', configuraton.java_path)

        else:
            QDesktopServices.openUrl(link)

    def update_crs_info(self):
        self.crsSelector.setCrs(self.crs)

    def crs_changed(self):
        if self.crsSelector.crs().authid()[:5] != 'EPSG:':
            self.crs_label.setStyleSheet('color: orange')
            self.crs_label.setToolTip(self.tr('Please select an EPSG Coordinate Reference System'))
            self.epsg = 21781
        else:
            self.crs_label.setStyleSheet('')
            self.crs_label.setToolTip(self.tr('Coordinate Reference System'))
            authid = self.crsSelector.crs().authid()
            self.epsg = int(authid[5:])
