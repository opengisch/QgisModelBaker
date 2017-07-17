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

from psycopg2 import OperationalError

from projectgenerator.gui.options import OptionsDialog
from projectgenerator.gui.ili2pg_options import Ili2pgOptionsDialog
from projectgenerator.libili2pg.ili2pg_config import ImportConfiguration
from projectgenerator.libili2pg.ilicache import IliCache
from projectgenerator.libili2pg.iliimporter import JavaNotFoundError
from projectgenerator.utils.qt_utils import make_file_selector, Validators, FileValidator
from qgis.PyQt.QtGui import QColor, QDesktopServices, QFont, QRegExpValidator, QValidator
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QApplication, QCompleter
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QRegExp, Qt
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from qgis.gui import QgsProjectionSelectionDialog
from ..utils import get_ui_class
from ..libili2pg import iliimporter
from ..libqgsprojectgen.generator.postgres import Generator
from ..libqgsprojectgen.dataobjects import Project

DIALOG_UI = get_ui_class('generate_project.ui')


class GenerateProjectDialog(QDialog, DIALOG_UI):
    def __init__(self, iface, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
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
        self.base_configuration = base_config

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        self.restore_configuration()

        self.validators = Validators()
        regexp = QRegExp("[a-zA-Z_0-9]+") # Non empty string
        validator = QRegExpValidator(regexp)
        fileValidator = FileValidator(pattern='*.ili')

        self.pg_host_line_edit.setValidator(validator)
        self.pg_database_line_edit.setValidator(validator)
        self.pg_user_line_edit.setValidator(validator)
        self.ili_file_line_edit.setValidator(fileValidator)

        self.pg_host_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_database_line_edit.textChanged.emit(self.pg_database_line_edit.text())
        self.pg_user_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_user_line_edit.textChanged.emit(self.pg_user_line_edit.text())
        self.ili_file_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.ili_file_line_edit.textChanged.emit(self.ili_file_line_edit.text())
        self.ilicache = IliCache(base_config)
        self.ilicache.models_changed.connect(self.update_models_completer)
        self.ilicache.new_message.connect(self.show_message)
        self.ilicache.refresh()


    def accepted(self):
        configuration = self.updated_configuration()

        if self.type_combo_box.currentData() == 'ili':
            if not self.ili_file_line_edit.validator().validate(configuration.ilifile, 0)[0] == QValidator.Acceptable \
                    and not self.ili_models_line_edit.text():
                self.txtStdout.setText(self.tr('Please set a valid INTERLIS file or model before creating the project.'))
                self.ili_file_line_edit.setFocus()
                return
        if not configuration.host:
            self.txtStdout.setText(self.tr('Please set a host before creating the project.'))
            self.pg_host_line_edit.setFocus()
            return
        if not configuration.database:
            self.txtStdout.setText(self.tr('Please set a database before creating the project.'))
            self.pg_database_line_edit.setFocus()
            return
        if not configuration.user:
            self.txtStdout.setText(self.tr('Please set a database user before creating the project.'))
            self.pg_user_line_edit.setFocus()
            return

        try:
            generator = Generator(configuration.uri, configuration.schema)
        except OperationalError:
            self.txtStdout.setText(self.tr('There was an error connecting to the database. Check connection parameters.'))
            return

        self.save_configuration(configuration)

        QApplication.setOverrideCursor( Qt.WaitCursor )
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()

        if self.type_combo_box.currentData() == 'ili':
            importer = iliimporter.Importer()

            importer.configuration = configuration
            importer.stdout.connect(self.print_info)
            importer.stderr.connect(self.on_stderr)
            importer.process_started.connect(self.on_process_started)
            importer.process_finished.connect(self.on_process_finished)

            try:
                if importer.run() != iliimporter.Importer.SUCCESS:
                    self.enable()
                    QApplication.restoreOverrideCursor()
                    return
            except JavaNotFoundError:
                self.txtStdout.setTextColor(QColor('#000000'))
                self.txtStdout.clear()
                self.txtStdout.setText(self.tr('Java could not be found. Please <a href="https://java.com/en/download/">install Java</a> and or <a href="#configure">configure a custom java path</a>. We also support the JAVA_HOME environment variable in case you prefer this.'))
                self.enable()
                QApplication.restoreOverrideCursor()
                return

            configuration.schema = configuration.schema or configuration.database

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

        self.buttonBox.clear()
        self.buttonBox.setEnabled(True)
        self.buttonBox.addButton(QDialogButtonBox.Close)

        QApplication.restoreOverrideCursor()

    def print_info(self, text):
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        self.txtStdout.setTextColor(QColor('#aa2222'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        self.txtStdout.setTextColor(QColor('#777777'))
        self.txtStdout.append('Finished ({})'.format(exit_code))

    def updated_configuration(self):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = ImportConfiguration()

        configuration.host = self.pg_host_line_edit.text().strip()
        configuration.user = self.pg_user_line_edit.text().strip()
        configuration.database = self.pg_database_line_edit.text().strip()
        configuration.schema = self.pg_schema_line_edit.text().strip().lower()
        configuration.password = self.pg_password_line_edit.text()
        configuration.ilifile = self.ili_file_line_edit.text().strip()
        configuration.ilimodels = self.ili_models_line_edit.text().strip()
        configuration.epsg = self.epsg
        configuration.inheritance = self.ili2pg_options.get_inheritance_type()
        configuration.java_path = QSettings().value('QgsProjectGenerator/java_path', '')
        configuration.base_configuration = self.base_configuration

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
            self.pg_schema_line_edit.setPlaceholderText("[Leave empty to create a default schema]")
        else:
            self.ili_config.hide()
            self.pg_schema_line_edit.setPlaceholderText("[Leave empty to load all schemas in the database]")

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgsProjectGenerator/ili2db')
                self.base_configuration.save(settings)

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

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ili_models_line_edit.setCompleter(completer)

    def show_message(self, level, message):
        if level == QgsMessageBar.WARNING:
            self.bar.pushMessage(message, QgsMessageBar.INFO, 10)
        elif level == QgsMessageBar.CRITICAL:
            self.bar.pushMessage(message, QgsMessageBar.WARNING, 10)
