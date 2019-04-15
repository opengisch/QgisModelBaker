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

import webbrowser

import re
from psycopg2 import OperationalError
from pyodbc import ProgrammingError

from QgisModelBaker.gui.options import OptionsDialog
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog
from QgisModelBaker.gui.multiple_models import MultipleModelsDialog
from QgisModelBaker.libili2db.globals import CRS_PATTERNS, displayDbIliMode
from QgisModelBaker.libili2db.ili2dbconfig import SchemaImportConfiguration
from QgisModelBaker.libili2db.ilicache import IliCache, ModelCompleterDelegate
from QgisModelBaker.libili2db.iliimporter import JavaNotFoundError
from QgisModelBaker.libili2db.ili2dbutils import color_log_text
from QgisModelBaker.utils.qt_utils import (
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
    QgsCoordinateReferenceSystem,
    Qgis
)
from qgis.gui import (
    QgsMessageBar,
    QgsGui
)
from ..utils import get_ui_class
from ..libili2db import iliimporter
from ..libili2db.globals import DbIliMode
from ..libqgsprojectgen.generator.generator import Generator
from ..libqgsprojectgen.dataobjects import Project
from ..libqgsprojectgen.dbconnector import pg_connector

DIALOG_UI = get_ui_class('generate_project.ui')


class GenerateProjectDialog(QDialog, DIALOG_UI):

    def __init__(self, iface, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.iface = iface
        QgsGui.instance().enableAutoGeometryRestore(self)
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
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)
        self.multiple_models_dialog = MultipleModelsDialog(self)
        self.multiple_models_button.clicked.connect(
            self.multiple_models_dialog.open)
        self.multiple_models_dialog.accepted.connect(
            self.fill_models_line_edit)
        self.type_combo_box.clear()
        self.type_combo_box.addItem(
            self.tr('Interlis (use PostGIS)'), DbIliMode.ili2pg)
        self.type_combo_box.addItem(
            self.tr('Interlis (use GeoPackage)'), DbIliMode.ili2gpkg)
        self.type_combo_box.addItem(
            self.tr('Interlis (use SQL Server)'), DbIliMode.ili2mssql)
        self.type_combo_box.addItem(self.tr(displayDbIliMode[DbIliMode.pg]), DbIliMode.pg)
        self.type_combo_box.addItem(self.tr(displayDbIliMode[DbIliMode.gpkg]), DbIliMode.gpkg)
        self.type_combo_box.addItem(self.tr(displayDbIliMode[DbIliMode.mssql]), DbIliMode.mssql)
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
        
        # mssql fields
        self.mssql_host_line_edit.setValidator(nonEmptyValidator)
        self.mssql_database_line_edit.setValidator(nonEmptyValidator)
        self.mssql_user_line_edit.setValidator(nonEmptyValidator)
        
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
        self.pg_use_super_login.setText(
            self.tr('Generate schema with superuser login from settings ({})').format(base_config.super_pg_user))
        self.ili_models_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili_models_line_edit.textChanged.emit(
            self.ili_models_line_edit.text())
        self.ili_models_line_edit.textChanged.connect(self.on_model_changed)
        self.ili_models_line_edit.textChanged.connect(self.complete_models_completer)
        self.ili_models_line_edit.punched.connect(self.complete_models_completer)
        
        # mssql fields
        self.mssql_host_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_host_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        self.mssql_database_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_database_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        self.mssql_user_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.mssql_user_line_edit.textChanged.emit(self.mssql_host_line_edit.text())
        
        self.ilicache = IliCache(self.base_configuration)
        self.refresh_ili_cache()
        self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model from repository]'))

        self.ili_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili_file_line_edit.textChanged.connect(self.ili_file_changed)
        self.ili_file_line_edit.textChanged.emit(
            self.ili_file_line_edit.text())

    def accepted(self):
        configuration = self.updated_configuration()

        if self.type_combo_box.currentData() & DbIliMode.ili: # it's an ili tool
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

        if self.type_combo_box.currentData() & DbIliMode.pg:
            if not configuration.dbhost:
                self.txtStdout.setText(
                    self.tr('Please set a host before creating the project.'))
                self.pg_host_line_edit.setFocus()
                return
            if not configuration.database:
                self.txtStdout.setText(
                    self.tr('Please set a database before creating the project.'))
                self.pg_database_line_edit.setFocus()
                return
            if not configuration.dbusr:
                self.txtStdout.setText(
                    self.tr('Please set a database user before creating the project.'))
                self.pg_user_line_edit.setFocus()
                return
        elif self.type_combo_box.currentData() & DbIliMode.mssql:
            if not configuration.dbhost:
                self.txtStdout.setText(
                    self.tr('Please set a host before creating the project.'))
                self.mssql_host_line_edit.setFocus()
                return
            if not configuration.database:
                self.txtStdout.setText(
                    self.tr('Please set a database before creating the project.'))
                self.mssql_database_line_edit.setFocus()
                return
            if not configuration.dbusr:
                self.txtStdout.setText(
                    self.tr('Please set a database user before creating the project.'))
                self.mssql_user_line_edit.setFocus()
                return
        elif self.type_combo_box.currentData() & DbIliMode.gpkg:
            if not configuration.dbfile or self.gpkg_file_line_edit.validator().validate(configuration.dbfile, 0)[0] != QValidator.Acceptable:
                self.txtStdout.setText(
                    self.tr('Please set a valid database file before creating the project.'))
                self.gpkg_file_line_edit.setFocus()
                return

        configuration.dbschema = configuration.dbschema or configuration.database
        self.save_configuration(configuration)

        # create schema with superuser
        if (self.type_combo_box.currentData() & DbIliMode.pg) and configuration.db_use_super_login:
            _db_connector = pg_connector.PGConnector(configuration.super_user_uri, configuration.dbschema)
            if not _db_connector.db_or_schema_exists():
                _db_connector.create_db_or_schema(configuration.dbusr)

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            self.disable()
            self.txtStdout.setTextColor(QColor('#000000'))
            self.txtStdout.clear()

            if self.type_combo_box.currentData() & DbIliMode.ili: # it's an ili tool
                importer = iliimporter.Importer()

                importer.tool = self.type_combo_box.currentData()
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
                except JavaNotFoundError as e:
                    self.txtStdout.setTextColor(QColor('#000000'))
                    self.txtStdout.clear()
                    self.txtStdout.setText(e.error_string)
                    self.enable()
                    self.progress_bar.hide()
                    return

            try:
                generator = Generator(configuration.tool, configuration.uri,
                                      configuration.inheritance, configuration.dbschema)
                self.progress_bar.setValue(50)
            except OperationalError:
                self.txtStdout.setText(
                    self.tr('There was an error connecting to the database. Check connection parameters.'))
                self.enable()
                self.progress_bar.hide()
                return
            except ProgrammingError:
                self.txtStdout.setText(
                    self.tr('There was an error connecting to the database. Check connection parameters.'))
                self.enable()
                self.progress_bar.hide()
                return

            if self.type_combo_box.currentData() & ~DbIliMode.ili: # No ili tool
                if not generator.db_or_schema_exists():
                    self.txtStdout.setText(
                        self.tr('Source {} does not exist. Check connection parameters.').format(
                            'database' if self.type_combo_box.currentData() == DbIliMode.gpkg else 'schema'
                        ))
                    self.enable()
                    self.progress_bar.hide()
                    return

            if self.type_combo_box.currentData() == DbIliMode.pg:
                if not generator._postgis_exists():
                    self.txtStdout.setText(
                        self.tr('The current database does not have PostGIS installed! Please install it by running `CREATE EXTENSION postgis;` on the database before proceeding.'))
                    self.enable()
                    self.progress_bar.hide()
                    return

            self.print_info(
                self.tr('\nObtaining available layers from the database…'))
            available_layers = generator.layers()

            if not available_layers:
                if self.type_combo_box.currentData() == DbIliMode.gpkg:
                    text = self.tr('The GeoPackage has no layers to load into QGIS.')
                else:
                    text = self.tr('The schema has no layers to load into QGIS.')
                self.txtStdout.setText(text)
                self.enable()
                self.progress_bar.hide()
                return

            self.progress_bar.setValue(70)
            self.print_info(
                self.tr('Obtaining relations from the database…'))
            relations, bags_of_enum = generator.relations(available_layers)
            self.progress_bar.setValue(75)
            self.print_info(self.tr('Arranging layers into groups…'))
            legend = generator.legend(available_layers)
            self.progress_bar.setValue(85)

            project = Project()
            project.layers = available_layers
            project.relations = relations
            project.bags_of_enum = bags_of_enum
            project.legend = legend
            self.print_info(self.tr('Configuring forms and widgets…'))
            project.post_generate()
            self.progress_bar.setValue(90)

            qgis_project = QgsProject.instance()

            self.print_info(self.tr('Generating QGIS project…'))
            project.create(None, qgis_project)

            # Set the extent of the mapCanvas from the first layer extent found
            for layer in project.layers:
                if layer.extent is not None:
                    self.iface.mapCanvas().setExtent(layer.extent)
                    self.iface.mapCanvas().refresh()
                    break

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
        color_log_text(text, self.txtStdout)
        self.advance_progress_bar_by_text(text)
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.txtStdout.setText(command)
        self.progress_bar.setValue(10)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        if exit_code == 0:
            color = '#004905'
            message = self.tr(
                'Interlis model(s) successfully imported into the database!')
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
        configuration = SchemaImportConfiguration()

        if self.type_combo_box.currentData() & DbIliMode.pg:
            # PostgreSQL specific options
            configuration.tool = DbIliMode.ili2pg
            configuration.dbhost = self.pg_host_line_edit.text().strip()
            configuration.dbport = self.pg_port_line_edit.text().strip()
            configuration.dbusr = self.pg_user_line_edit.text().strip()
            configuration.database = "'{}'".format(self.pg_database_line_edit.text().strip())
            configuration.dbschema = self.pg_schema_line_edit.text().strip().lower()
            configuration.dbpwd = self.pg_password_line_edit.text()
            configuration.db_use_super_login = self.pg_use_super_login.isChecked()
        elif self.type_combo_box.currentData() & DbIliMode.mssql:
            configuration.tool = DbIliMode.ili2mssql
            configuration.dbhost = self.mssql_host_line_edit.text().strip()
            configuration.dbinstance = self.mssql_instance_line_edit.text().strip()
            configuration.dbport = self.mssql_port_line_edit.text().strip()
            configuration.dbusr = self.mssql_user_line_edit.text().strip()
            configuration.database = self.mssql_database_line_edit.text().strip()
            configuration.dbschema = self.mssql_schema_line_edit.text().strip().lower()
            configuration.dbpwd = self.mssql_password_line_edit.text()
        elif self.type_combo_box.currentData() & DbIliMode.gpkg:
            configuration.tool = DbIliMode.ili2gpkg
            configuration.dbfile = self.gpkg_file_line_edit.text().strip()

        configuration.epsg = self.epsg
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.tomlfile = self.ili2db_options.toml_file()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()

        configuration.base_configuration = self.base_configuration
        if self.ili_file_line_edit.text().strip():
            configuration.ilifile = self.ili_file_line_edit.text().strip()

        if self.ili_models_line_edit.text().strip():
            configuration.ilimodels = self.ili_models_line_edit.text().strip()

        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgisModelBaker/ili2db/ilifile',
                          configuration.ilifile)
        settings.setValue('QgisModelBaker/ili2db/epsg', self.epsg)
        settings.setValue('QgisModelBaker/importtype',
                          self.type_combo_box.currentData().value)
        if self.type_combo_box.currentData() & DbIliMode.pg:
            # PostgreSQL specific options
            settings.setValue(
                'QgisModelBaker/ili2pg/host', configuration.dbhost)
            settings.setValue(
                'QgisModelBaker/ili2pg/port', configuration.dbport)
            settings.setValue(
                'QgisModelBaker/ili2pg/user', configuration.dbusr)
            settings.setValue(
                'QgisModelBaker/ili2pg/database', configuration.database.strip("'"))
            settings.setValue(
                'QgisModelBaker/ili2pg/schema', configuration.dbschema)
            settings.setValue(
                'QgisModelBaker/ili2pg/password', configuration.dbpwd)
            settings.setValue(
                'QgisModelBaker/ili2pg/usesuperlogin', configuration.db_use_super_login)
        elif self.type_combo_box.currentData() & DbIliMode.mssql:
            settings.setValue(
                'QgisModelBaker/ili2mssql/host', configuration.dbhost)
            settings.setValue(
                'QgisModelBaker/ili2mssql/instance', configuration.dbinstance)
            settings.setValue(
                'QgisModelBaker/ili2mssql/port', configuration.dbport)
            settings.setValue('QgisModelBaker/ili2mssql/user', configuration.dbusr)
            settings.setValue(
                'QgisModelBaker/ili2mssql/database', configuration.database)
            settings.setValue(
                'QgisModelBaker/ili2mssql/schema', configuration.dbschema)
            settings.setValue('QgisModelBaker/ili2mssql/password', configuration.dbpwd)

        elif self.type_combo_box.currentData() & DbIliMode.gpkg:
            settings.setValue(
                'QgisModelBaker/ili2gpkg/dbfile', configuration.dbfile)

    def restore_configuration(self):
        settings = QSettings()

        self.ili_file_line_edit.setText(
            settings.value('QgisModelBaker/ili2db/ilifile'))
        self.crs = QgsCoordinateReferenceSystem(
            settings.value('QgisModelBaker/ili2db/epsg', 21781, int))
        self.fill_toml_file_info_label()
        self.update_crs_info()

        self.pg_host_line_edit.setText(
            settings.value('QgisModelBaker/ili2pg/host', 'localhost'))
        self.pg_port_line_edit.setText(
            settings.value('QgisModelBaker/ili2pg/port'))
        self.pg_user_line_edit.setText(
            settings.value('QgisModelBaker/ili2pg/user'))
        self.pg_database_line_edit.setText(
            settings.value('QgisModelBaker/ili2pg/database'))
        self.pg_schema_line_edit.setText(
            settings.value('QgisModelBaker/ili2pg/schema'))
        self.pg_password_line_edit.setText(
            settings.value('QgisModelBaker/ili2pg/password'))
        self.pg_use_super_login.setChecked(
            settings.value('QgisModelBaker/ili2pg/usesuperlogin', defaultValue=False, type=bool))
        
        self.mssql_host_line_edit.setText(settings.value(
            'QgisModelBaker/ili2mssql/host', 'localhost'))
        self.mssql_instance_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/instance'))
        self.mssql_port_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/port'))
        self.mssql_user_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/user'))
        self.mssql_database_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/database'))
        self.mssql_schema_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/schema'))
        self.mssql_password_line_edit.setText(
            settings.value('QgisModelBaker/ili2mssql/password'))
            
        self.gpkg_file_line_edit.setText(
            settings.value('QgisModelBaker/ili2gpkg/dbfile'))

        import_type_val = int(settings.value('QgisModelBaker/importtype', DbIliMode.pg))
        mode = DbIliMode(import_type_val) if DbIliMode(import_type_val) in DbIliMode else DbIliMode.pg

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
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
        if self.type_combo_box.currentData() == DbIliMode.ili2pg:
            self.ili_config.show()
            self.pg_config.show()
            self.gpkg_config.hide()
            self.mssql_config.hide()
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]"))
        elif self.type_combo_box.currentData() == DbIliMode.pg:
            self.ili_config.hide()
            self.pg_config.show()
            self.gpkg_config.hide()
            self.mssql_config.hide()
            self.pg_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to load all schemas in the database]"))
        if self.type_combo_box.currentData() == DbIliMode.ili2mssql:
            self.ili_config.show()
            self.pg_config.hide()
            self.gpkg_config.hide()
            self.mssql_config.show()
            self.mssql_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to create a default schema]"))
        elif self.type_combo_box.currentData() == DbIliMode.gpkg:
            self.ili_config.hide()
            self.pg_config.hide()
            self.gpkg_config.show()
            self.mssql_config.hide()
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
        elif self.type_combo_box.currentData() == DbIliMode.mssql:
            self.ili_config.hide()
            self.pg_config.hide()
            self.gpkg_config.hide()
            self.mssql_config.show()
            self.mssql_schema_line_edit.setPlaceholderText(
                self.tr("[Leave empty to load all schemas in the database]"))
        elif self.type_combo_box.currentData() == DbIliMode.ili2gpkg:
            self.ili_config.show()
            self.pg_config.hide()
            self.gpkg_config.show()
            self.mssql_config.hide()
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
        if not text:
            return
        for pattern, crs in CRS_PATTERNS.items():
            if re.search(pattern, text):
                self.crs = QgsCoordinateReferenceSystem(crs)
                self.update_crs_info()
                break
        self.ili2db_options.set_toml_file_key(text)
        self.fill_toml_file_info_label()

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgisModelBaker/ili2db')
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
            self.ilicache = IliCache(None, self.ili_file_line_edit.text().strip())
            self.refresh_ili_cache()
            models = self.ilicache.process_ili_file(self.ili_file_line_edit.text().strip())
            self.ili_models_line_edit.setText(models[-1]['name'])
            self.ili_models_line_edit.setPlaceholderText(models[-1]['name'])
        else:
            nonEmptyValidator = NonEmptyStringValidator()
            self.ili_models_line_edit.setValidator(nonEmptyValidator)
            self.ili_models_line_edit.textChanged.emit(
                self.ili_models_line_edit.text())

            # Update completer to add models from given ili file
            self.ilicache = IliCache(self.base_configuration)
            self.refresh_ili_cache()
            self.ili_models_line_edit.setPlaceholderText(self.tr('[Search model from repository]'))

    def refresh_ili_cache(self):
        self.ilicache.new_message.connect(self.show_message)
        self.ilicache.refresh()
        self.update_models_completer()

    def complete_models_completer(self):
        if not self.ili_models_line_edit.text():
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.ili_models_line_edit.completer().complete()
        else:
            self.ili_models_line_edit.completer().setCompletionMode(QCompleter.PopupCompletion)

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model, self.ili_models_line_edit)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.delegate = ModelCompleterDelegate()
        completer.popup().setItemDelegate(self.delegate)
        self.ili_models_line_edit.setCompleter(completer)
        self.multiple_models_dialog.models_line_edit.setCompleter(completer)

    def show_message(self, level, message):
        if level == Qgis.Warning:
            self.bar.pushMessage(message, Qgis.Info, 10)
        elif level == Qgis.Critical:
            self.bar.pushMessage(message, Qgis.Warning, 10)

    def fill_models_line_edit(self):
        self.ili_models_line_edit.setText(
            self.multiple_models_dialog.get_models_string())

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/{}/user-guide.html#generate-project".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/user-guide.html#generate-project")

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models…':
            self.progress_bar.setValue(20)
        elif text.strip() == 'Info: create table structure…':
            self.progress_bar.setValue(30)
