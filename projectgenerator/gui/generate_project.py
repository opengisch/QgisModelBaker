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
import webbrowser

import re
from psycopg2 import OperationalError

from projectgenerator.gui.options import OptionsDialog
from projectgenerator.gui.ili2db_options import Ili2dbOptionsDialog
from projectgenerator.gui.multiple_models import MultipleModelsDialog
from projectgenerator.libili2db.globals import CRS_PATTERNS
from projectgenerator.libili2db.ili2dbconfig import ImportConfiguration
from projectgenerator.libili2db.ilicache import IliCache
from projectgenerator.libili2db.iliimporter import JavaNotFoundError
from projectgenerator.utils.qt_utils import (
    make_file_selector,
    make_save_file_selector,
    Validators,
    FileValidator,
    NonEmptyStringValidator,
    OverrideCursor
)
from qgis.PyQt.QtGui import (
    QColor,
    QDesktopServices,
    QValidator
)
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QCompleter,
    QSizePolicy,
    QGridLayout
)
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    Qt,
    QLocale
)
from qgis.core import (
    QgsProject,
    QgsCoordinateReferenceSystem
)
from qgis.gui import QgsMessageBar
from ..utils import get_ui_class
from ..libili2db import iliimporter
from ..libqgsprojectgen.generator.generator import Generator
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
        create_button = self.buttonBox.addButton(
            self.tr('Create'), QDialogButtonBox.AcceptRole)
        create_button.setDefault(True)
        self.ili_file_browse_button.clicked.connect(
            make_file_selector(self.ili_file_line_edit, title=self.tr('Open Interlis Model'),
                               file_filter=self.tr('Interlis Model File (*.ili)')))
        self.buttonBox.addButton(QDialogButtonBox.Help)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.crs = QgsCoordinateReferenceSystem()
        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.multiple_models_dialog = MultipleModelsDialog(self)
        self.multiple_models_button.clicked.connect(
            self.multiple_models_dialog.open)
        self.multiple_models_dialog.accepted.connect(
            self.fill_models_line_edit)
        self.type_combo_box.clear()
        self.type_combo_box.addItem(
            self.tr('Interlis (use PostGIS)'), 'ili2pg')
        self.type_combo_box.addItem(
            self.tr('Interlis (use GeoPackage)'), 'ili2gpkg')
        self.type_combo_box.addItem(self.tr('PostGIS'), 'pg')
        self.type_combo_box.addItem(self.tr('GeoPackage'), 'gpkg')
        self.type_combo_box.currentIndexChanged.connect(self.type_changed)
        self.txtStdout.anchorClicked.connect(self.link_activated)
        self.crsSelector.crsChanged.connect(self.crs_changed)
        self.base_configuration = base_config

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()
        fileValidator = FileValidator(pattern='*.ili', allow_empty=True)
        self.gpkgSaveFileValidator = FileValidator(
            pattern='*.gpkg', allow_non_existing=True)
        self.gpkgOpenFileValidator = FileValidator(pattern='*.gpkg')
        self.gpkg_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)

        self.restore_configuration()

        self.ili_models_line_edit.setValidator(nonEmptyValidator)
        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)
        self.pg_user_line_edit.setValidator(nonEmptyValidator)
        self.ili_file_line_edit.setValidator(fileValidator)

        self.pg_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_database_line_edit.textChanged.emit(
            self.pg_database_line_edit.text())
        self.pg_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.pg_user_line_edit.textChanged.emit(self.pg_user_line_edit.text())
        self.ili_models_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili_models_line_edit.textChanged.emit(
            self.ili_models_line_edit.text())
        self.ili_models_line_edit.textChanged.connect(self.on_model_changed)

        self.ilicache = IliCache(base_config)
        self.ilicache.models_changed.connect(self.update_models_completer)
        self.ilicache.new_message.connect(self.show_message)
        self.ilicache.refresh()

        self.ili_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili_file_line_edit.textChanged.connect(self.ili_file_changed)
        self.ili_file_line_edit.textChanged.emit(
            self.ili_file_line_edit.text())

    def accepted(self):
        configuration = self.updated_configuration()

        if self.type_combo_box.currentData() in ['ili2pg', 'ili2gpkg']:
            if not self.ili_file_line_edit.text().strip():
                if not self.ili_models_line_edit.text().strip():
                    self.txtStdout.setText(
                        self.tr('Please set a valid INTERLIS model before creating the project.'))
                    self.ili_models_line_edit.setFocus()
                    return

            if self.ili_file_line_edit.text().strip() and \
                    self.ili_file_line_edit.validator().validate(configuration.ilifile, 0)[0] != QValidator.Acceptable:
                self.txtStdout.setText(
                    self.tr('Please set a valid INTERLIS file before creating the project.'))
                self.ili_file_line_edit.setFocus()
                return

        if self.type_combo_box.currentData() in ['ili2pg', 'pg']:
            if not configuration.host:
                self.txtStdout.setText(
                    self.tr('Please set a host before creating the project.'))
                self.pg_host_line_edit.setFocus()
                return
            if not configuration.database:
                self.txtStdout.setText(
                    self.tr('Please set a database before creating the project.'))
                self.pg_database_line_edit.setFocus()
                return
            if not configuration.user:
                self.txtStdout.setText(
                    self.tr('Please set a database user before creating the project.'))
                self.pg_user_line_edit.setFocus()
                return
        elif self.type_combo_box.currentData() in ['ili2gpkg', 'gpkg']:
            if not configuration.dbfile or self.gpkg_file_line_edit.validator().validate(configuration.dbfile, 0)[0] != QValidator.Acceptable:
                self.txtStdout.setText(
                    self.tr('Please set a valid database file before creating the project.'))
                self.gpkg_file_line_edit.setFocus()
                return

        self.save_configuration(configuration)

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            self.disable()
            self.txtStdout.setTextColor(QColor('#000000'))
            self.txtStdout.clear()

            if self.type_combo_box.currentData() in ['ili2pg', 'ili2gpkg']:
                importer = iliimporter.Importer()

                importer.tool_name = self.type_combo_box.currentData()
                importer.configuration = configuration
                importer.stdout.connect(self.print_info)
                importer.stderr.connect(self.on_stderr)
                importer.process_started.connect(self.on_process_started)
                importer.process_finished.connect(self.on_process_finished)

                try:
                    if importer.run() != iliimporter.Importer.SUCCESS:
                        self.enable()
                        self.progress_bar.hide()
                        return
                except JavaNotFoundError:
                    self.txtStdout.setTextColor(QColor('#000000'))
                    self.txtStdout.clear()
                    self.txtStdout.setText(self.tr(
                        'Java could not be found. Please <a href="https://java.com/en/download/">install Java</a> and or <a href="#configure">configure a custom java path</a>. We also support the JAVA_HOME environment variable in case you prefer this.'))
                    self.enable()
                    self.progress_bar.hide()
                    return

                configuration.schema = configuration.schema or configuration.database

            print(configuration.tool_name, configuration.uri, configuration)
            try:
                generator = Generator(configuration.tool_name, configuration.uri,
                                      configuration.inheritance, configuration.schema)
                self.progress_bar.setValue(50)
            except OperationalError:
                self.txtStdout.setText(
                    self.tr('There was an error connecting to the database. Check connection parameters.'))
                self.progress_bar.hide()
                return

            self.print_info(self.tr('\nObtaining available layers from the database...'))
            available_layers = generator.layers()
            self.progress_bar.setValue(70)
            self.print_info(self.tr('Obtaining relations from the database...'))
            relations = generator.relations(available_layers)
            self.progress_bar.setValue(75)
            self.print_info(self.tr('Arranging layers into groups...'))
            legend = generator.legend(available_layers)
            self.progress_bar.setValue(85)

            project = Project()
            project.layers = available_layers
            project.relations = relations
            project.legend = legend
            self.print_info(self.tr('Configuring forms and widgets...'))
            project.post_generate()
            self.progress_bar.setValue(90)

            qgis_project = QgsProject.instance()

            self.print_info(self.tr('Generating QGIS project...'))
            project.create(None, qgis_project)

            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
            self.progress_bar.setValue(100)
            self.print_info(self.tr('\nDone!'), '#004905')

    def print_info(self, text, text_color='#000000'):
        self.txtStdout.setTextColor(QColor(text_color))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        self.txtStdout.setTextColor(QColor('#2a2a2a'))
        self.txtStdout.append(text)
        self.advance_progress_bar_by_text(text)
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.txtStdout.setText(command)
        self.progress_bar.setValue(10)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        if exit_code == 0:
            color = '#004905'
            message = self.tr('Interlis model(s) successfully imported into the database!')
        else:
            color = '#aa2222'
            message = self.tr('Finished with errors!')

        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append(message)
        self.progress_bar.setValue(50)

    def updated_configuration(self):
        """
        Get the configuration that is updated with the user configuration changes on the dialog.
        :return: Configuration
        """
        configuration = ImportConfiguration()

        if self.type_combo_box.currentData() in ['ili2pg', 'pg']:
            # PostgreSQL specific options
            configuration.tool_name = 'ili2pg'
            configuration.host = self.pg_host_line_edit.text().strip()
            configuration.port = self.pg_port_line_edit.text().strip()
            configuration.user = self.pg_user_line_edit.text().strip()
            configuration.database = self.pg_database_line_edit.text().strip()
            configuration.schema = self.pg_schema_line_edit.text().strip().lower()
            configuration.password = self.pg_password_line_edit.text()
        elif self.type_combo_box.currentData() in ['ili2gpkg', 'gpkg']:
            configuration.tool_name = 'ili2gpkg'
            configuration.dbfile = self.gpkg_file_line_edit.text().strip()

        configuration.epsg = self.epsg
        configuration.inheritance = self.ili2db_options.get_inheritance_type()

        configuration.base_configuration = self.base_configuration
        if self.ili_file_line_edit.text().strip():
            configuration.ilifile = self.ili_file_line_edit.text().strip()

        if self.ili_models_line_edit.text().strip():
            configuration.ilimodels = self.ili_models_line_edit.text().strip()

        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgsProjectGenerator/ili2db/ilifile',
                          configuration.ilifile)
        settings.setValue('QgsProjectGenerator/ili2db/epsg', self.epsg)
        settings.setValue('QgsProjectGenerator/importtype',
                          self.type_combo_box.currentData())
        if self.type_combo_box.currentData() in ['ili2pg', 'pg']:
            # PostgreSQL specific options
            settings.setValue(
                'QgsProjectGenerator/ili2pg/host', configuration.host)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/port', configuration.port)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/user', configuration.user)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/database', configuration.database)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/schema', configuration.schema)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/password', configuration.password)
        elif self.type_combo_box.currentData() in ['ili2gpkg', 'gpkg']:
            settings.setValue(
                'QgsProjectGenerator/ili2gpkg/dbfile', configuration.dbfile)

    def restore_configuration(self):
        settings = QSettings()

        self.ili_file_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2db/ilifile'))
        self.crs = QgsCoordinateReferenceSystem(settings.value(
            'QgsProjectGenerator/ili2db/epsg', 21781, int))
        self.update_crs_info()

        self.pg_host_line_edit.setText(settings.value(
            'QgsProjectGenerator/ili2pg/host', 'localhost'))
        self.pg_port_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2pg/port'))
        self.pg_user_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2pg/user'))
        self.pg_database_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2pg/database'))
        self.pg_schema_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2pg/schema'))
        self.pg_password_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2pg/password'))
        self.gpkg_file_line_edit.setText(
            settings.value('QgsProjectGenerator/ili2gpkg/dbfile'))

        self.type_combo_box.setCurrentIndex(
            self.type_combo_box.findData(settings.value('QgsProjectGenerator/importtype', 'pg')))
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
        self.progress_bar.hide()
        if self.type_combo_box.currentData() == 'ili2pg':
            self.ili_config.show()
            self.pg_config.show()
            self.gpkg_config.hide()
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]"))
        elif self.type_combo_box.currentData() == 'pg':
            self.ili_config.hide()
            self.pg_config.show()
            self.gpkg_config.hide()
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to load all schemas in the database]"))
        elif self.type_combo_box.currentData() == 'gpkg':
            self.ili_config.hide()
            self.pg_config.hide()
            self.gpkg_config.show()
            self.gpkg_file_line_edit.setValidator(self.gpkgOpenFileValidator)
            self.gpkg_file_line_edit.textChanged.emit(
                self.gpkg_file_line_edit.text())
            try:
                self.gpkg_file_browse_button.clicked.disconnect()
            except:
                pass
            self.gpkg_file_browse_button.clicked.connect(
                make_file_selector(self.gpkg_file_line_edit, title=self.tr('Open GeoPackage database file'),
                                   file_filter=self.tr('GeoPackage Database (*.gpkg)')))
        elif self.type_combo_box.currentData() == 'ili2gpkg':
            self.ili_config.show()
            self.pg_config.hide()
            self.gpkg_config.show()
            self.gpkg_file_line_edit.setValidator(self.gpkgSaveFileValidator)
            self.gpkg_file_line_edit.textChanged.emit(
                self.gpkg_file_line_edit.text())
            try:
                self.gpkg_file_browse_button.clicked.disconnect()
            except:
                pass
            self.gpkg_file_browse_button.clicked.connect(
                make_save_file_selector(self.gpkg_file_line_edit, title=self.tr('Open GeoPackage database file'),
                                        file_filter=self.tr('GeoPackage Database (*.gpkg)'), extension='.gpkg'))

    def on_model_changed(self, text):
        for pattern, crs in CRS_PATTERNS.items():
            if re.search(pattern, text):
                self.crs = QgsCoordinateReferenceSystem(crs)
                self.update_crs_info()
                break

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
            self.crs_label.setToolTip(
                self.tr('Please select an EPSG Coordinate Reference System'))
            self.epsg = 21781
        else:
            self.crs_label.setStyleSheet('')
            self.crs_label.setToolTip(self.tr('Coordinate Reference System'))
            authid = self.crsSelector.crs().authid()
            self.epsg = int(authid[5:])

    def ili_file_changed(self):
        # If ili file is valid, models is optional
        if self.ili_file_line_edit.text().strip() and \
                self.ili_file_line_edit.validator().validate(self.ili_file_line_edit.text().strip(), 0)[0] == QValidator.Acceptable:
            self.ili_models_line_edit.setValidator(None)
            self.ili_models_line_edit.textChanged.emit(
                self.ili_models_line_edit.text())

            # Update completer to add models from given ili file
            self.iliFileCache = IliCache(
                self.base_configuration, self.ili_file_line_edit.text().strip())
            self.iliFileCache.models_changed.connect(
                self.update_models_completer)
            self.iliFileCache.new_message.connect(self.show_message)
            self.iliFileCache.refresh()
        else:
            nonEmptyValidator = NonEmptyStringValidator()
            self.ili_models_line_edit.setValidator(nonEmptyValidator)
            self.ili_models_line_edit.textChanged.emit(
                self.ili_models_line_edit.text())

            # Update completer to show repository models in models dir
            self.ilicache.models_changed.emit()

    def update_models_completer(self):
        completer = QCompleter(self.sender().model_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ili_models_line_edit.setCompleter(completer)
        self.multiple_models_dialog.models_line_edit.setCompleter(completer)

    def show_message(self, level, message):
        if level == QgsMessageBar.WARNING:
            self.bar.pushMessage(message, QgsMessageBar.INFO, 10)
        elif level == QgsMessageBar.CRITICAL:
            self.bar.pushMessage(message, QgsMessageBar.WARNING, 10)

    def fill_models_line_edit(self):
        self.ili_models_line_edit.setText(
            self.multiple_models_dialog.get_models_string())

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/projectgenerator/docs/{}/user-guide.html#generate-project".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/projectgenerator/docs/user-guide.html#generate-project")

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models...':
            self.progress_bar.setValue(20)
        elif text.strip() == 'Info: create table structure...':
            self.progress_bar.setValue(30)
