# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/05/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo (BSF-Swissphoto)
        email                : gcarrillo@linuxmail.org
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
import os.path
import re

from projectgenerator.gui.options import OptionsDialog, ModelListView
from projectgenerator.gui.multiple_models import MultipleModelsDialog
from projectgenerator.libili2db.iliexporter import JavaNotFoundError
from projectgenerator.libili2db.ilicache import IliCache, ModelCompleterDelegate
from projectgenerator.utils.qt_utils import make_save_file_selector, Validators, \
    make_file_selector, FileValidator, NonEmptyStringValidator, make_folder_selector, OverrideCursor
from qgis.PyQt.QtGui import QColor, QDesktopServices, QFont, QValidator
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QApplication, QCompleter, QMessageBox
from qgis.PyQt.QtCore import QCoreApplication, QSettings, Qt, QLocale, QStringListModel, QTimer
from qgis.core import QgsProject
from qgis.gui import QgsGui
from ..utils import get_ui_class
from ..libili2db import iliexporter, ili2dbconfig
from ..libqgsprojectgen.dbconnector import pg_connector, gpkg_connector

DIALOG_UI = get_ui_class('export.ui')


class ExportModels(QStringListModel):

    def __init__(self, tool_name, uri, schema=None):
        super().__init__()

        modelnames = list()
        try:
            if tool_name == 'ili2gpkg':
                self._db_connector = gpkg_connector.GPKGConnector(uri, None)
            else:
                self._db_connector = pg_connector.PGConnector(uri, schema)

            if self._db_connector.db_or_schema_exists():
                db_models = self._db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r'\{[^\}]*\}')
                    for modelname in regex.split(db_model['modelname']):
                        if modelname:
                            modelnames.append(modelname.strip())
        except:
            pass
        self.setStringList(modelnames)

        self._checked_models = {modelname: Qt.Checked for modelname in modelnames}

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            return self._checked_models[self.data(index, Qt.DisplayRole)]
        else:
            return QStringListModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self._checked_models[self.data(index, Qt.DisplayRole)] = data
        else:
            QStringListModel.setData(self, index, role, data)

    def check(self, index):
        if self.data( index, Qt.CheckStateRole ) == Qt.Checked:
            self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
        else:
            self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def checked_models(self):
        return [modelname for modelname in self.stringList() if self._checked_models[modelname] == Qt.Checked]

class ExportDialog(QDialog, DIALOG_UI):
    ValidExtensions = ['xtf', 'itf', 'gml', 'xml']

    def __init__(self, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        QgsGui.instance().enableAutoGeometryRestore(self);
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.addButton(
            self.tr('Export'), QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(QDialogButtonBox.Help)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.xtf_file_browse_button.clicked.connect(
            make_save_file_selector(self.xtf_file_line_edit, title=self.tr('Save in XTF Transfer File'),
                                    file_filter=self.tr('XTF Transfer File (*.xtf);;Interlis 1 Transfer File (*.itf);;XML (*.xml);;GML (*.gml)'), extension='.xtf', extensions=['.' + ext for ext in self.ValidExtensions]))
        self.xtf_file_browse_button.clicked.connect(
            self.xtf_browser_opened_to_true)
        self.xtf_browser_was_opened = False

        self.gpkg_file_browse_button.clicked.connect(
            make_file_selector(self.gpkg_file_line_edit, title=self.tr('Open GeoPackage database file'),
                               file_filter=self.tr('GeoPackage Database (*.gpkg)')))
        self.type_combo_box.clear()
        self.type_combo_box.addItem(self.tr('PostGIS'), 'pg')
        self.type_combo_box.addItem(self.tr('GeoPackage'), 'gpkg')
        self.type_combo_box.currentIndexChanged.connect(self.type_changed)

        self.base_configuration = base_config
        self.restore_configuration()

        self.validators = Validators()
        nonEmptyValidator = NonEmptyStringValidator()
        fileValidator = FileValidator(pattern=['*.' + ext for ext in self.ValidExtensions], allow_non_existing=True)
        gpkgFileValidator = FileValidator(pattern='*.gpkg')

        self.pg_host_line_edit.setValidator(nonEmptyValidator)
        self.pg_database_line_edit.setValidator(nonEmptyValidator)
        self.pg_user_line_edit.setValidator(nonEmptyValidator)
        self.xtf_file_line_edit.setValidator(fileValidator)
        self.gpkg_file_line_edit.setValidator(gpkgFileValidator)

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
        self.xtf_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.xtf_file_line_edit.textChanged.connect(
            self.xtf_browser_opened_to_false)
        self.xtf_file_line_edit.textChanged.emit(
            self.xtf_file_line_edit.text())
        self.gpkg_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.gpkg_file_line_edit.textChanged.emit(
            self.gpkg_file_line_edit.text())

        #refresh the models on changing values but avoid massive db connects by timer
        self.refreshTimer = QTimer()
        self.refreshTimer.setSingleShot(True)
        self.refreshTimer.timeout.connect( self.refresh_models)
        self.pg_host_line_edit.textChanged.connect(self.request_for_refresh_models)
        self.pg_port_line_edit.textChanged.connect(self.request_for_refresh_models)
        self.pg_database_line_edit.textChanged.connect(self.request_for_refresh_models)
        self.pg_schema_line_edit.textChanged.connect(self.request_for_refresh_models)
        self.pg_user_line_edit.textChanged.connect(self.request_for_refresh_models)
        self.pg_password_line_edit.textChanged.connect(self.request_for_refresh_models)
        self.gpkg_file_line_edit.textChanged.connect(self.request_for_refresh_models)

        self.export_models_model = ExportModels(None, None, None)
        self.refreshed_export_models_model()
        self.export_models_view.setModel(self.export_models_model)
        self.export_models_view.clicked.connect(self.export_models_model.check)
        self.export_models_view.spaced.connect(self.export_models_model.check)

    def request_for_refresh_models(self):
        #hold refresh back one second
        self.refreshTimer.start(500)

    def refresh_models(self):
        self.export_models_model=self.refreshed_export_models_model()
        self.export_models_view.setModel(self.export_models_model)
        self.export_models_view.clicked.connect(self.export_models_model.click)

    def refreshed_export_models_model(self):
        tool_name = 'ili2pg' if self.type_combo_box.currentData() == 'pg' else 'ili2gpkg'
        uri = []
        if tool_name == 'ili2pg':
            uri += ['dbname={}'.format(self.updated_configuration().database)]
            uri += ['user={}'.format(self.updated_configuration().dbusr)]
            if self.updated_configuration().dbpwd:
                uri += ['password={}'.format(self.updated_configuration().dbpwd)]
            uri += ['host={}'.format(self.updated_configuration().dbhost)]
            if self.updated_configuration().dbport:
                uri += ['port={}'.format(self.updated_configuration().dbport)]
        elif tool_name == 'ili2gpkg':
            uri = [self.updated_configuration().dbfile]
        uri_string = ' '.join(uri)

        schema = self.updated_configuration().dbschema

        self.export_models_model = ExportModels(tool_name, uri_string, schema)
        return self.export_models_model

    def accepted(self):
        configuration = self.updated_configuration()

        if not self.xtf_file_line_edit.validator().validate(configuration.xtffile, 0)[0] == QValidator.Acceptable:
            self.txtStdout.setText(
                self.tr('Please set a valid INTERLIS XTF file before exporting data.'))
            self.xtf_file_line_edit.setFocus()
            return
        if not configuration.ilimodels:
            self.txtStdout.setText(
                self.tr('Please set a model before exporting data.'))
            self.export_models_view.setFocus()
            return

        if self.type_combo_box.currentData() == 'pg':
            if not configuration.dbhost:
                self.txtStdout.setText(
                    self.tr('Please set a host before exporting data.'))
                self.pg_host_line_edit.setFocus()
                return
            if not configuration.database:
                self.txtStdout.setText(
                    self.tr('Please set a database before exporting data.'))
                self.pg_database_line_edit.setFocus()
                return
            if not configuration.dbusr:
                self.txtStdout.setText(
                    self.tr('Please set a database user before exporting data.'))
                self.pg_user_line_edit.setFocus()
                return
        elif self.type_combo_box.currentData() == 'gpkg':
            if not configuration.dbfile or self.gpkg_file_line_edit.validator().validate(configuration.dbfile, 0)[0] != QValidator.Acceptable:
                self.txtStdout.setText(
                    self.tr('Please set an existing database file before creating the project.'))
                self.gpkg_file_line_edit.setFocus()
                return

        # If xtf browser was opened and the file exists, the user already chose
        # to overwrite the file
        if os.path.isfile(self.xtf_file_line_edit.text().strip()) and not self.xtf_browser_was_opened:
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setText(self.tr("{filename} already exists.\nDo you want to replace it?").format(filename=os.path.basename(self.xtf_file_line_edit.text().strip())))
            self.msg.setWindowTitle(self.tr("Save in XTF Transfer File"))
            self.msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box = self.msg.exec_()
            if msg_box == QMessageBox.No:
                return

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.show()
            self.progress_bar.setValue(0)

            self.disable()
            self.txtStdout.setTextColor(QColor('#000000'))
            self.txtStdout.clear()

            exporter = iliexporter.Exporter()

            tool_name = 'ili2pg' if self.type_combo_box.currentData() == 'pg' else 'ili2gpkg'
            exporter.tool_name = tool_name
            exporter.configuration = configuration

            self.save_configuration(configuration)

            exporter.stdout.connect(self.print_info)
            exporter.stderr.connect(self.on_stderr)
            exporter.process_started.connect(self.on_process_started)
            exporter.process_finished.connect(self.on_process_finished)

            self.progress_bar.setValue(25)

            try:
                if exporter.run() != iliexporter.Exporter.SUCCESS:
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

            self.buttonBox.clear()
            self.buttonBox.setEnabled(True)
            self.buttonBox.addButton(QDialogButtonBox.Close)
            self.progress_bar.setValue(100)

    def print_info(self, text):
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        self.txtStdout.setTextColor(QColor('#2a2a2a'))
        self.txtStdout.append(text)
        self.advance_progress_bar_by_text(text)
        QCoreApplication.processEvents()

    def on_process_started(self, command):
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        color = '#004905' if exit_code == 0 else '#aa2222'
        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append(self.tr('Finished ({})'.format(exit_code)))
        if result == iliexporter.Exporter.SUCCESS:
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
        configuration = ili2dbconfig.ExportConfiguration()

        if self.type_combo_box.currentData() == 'pg':
            # PostgreSQL specific options
            configuration.dbhost = self.pg_host_line_edit.text().strip()
            configuration.dbport = self.pg_port_line_edit.text().strip()
            configuration.dbusr = self.pg_user_line_edit.text().strip()
            configuration.database = self.pg_database_line_edit.text().strip()
            configuration.dbschema = self.pg_schema_line_edit.text().strip().lower()
            configuration.dbpwd = self.pg_password_line_edit.text()
        elif self.type_combo_box.currentData() == 'gpkg':
            configuration.dbfile = self.gpkg_file_line_edit.text().strip()

        configuration.xtffile = self.xtf_file_line_edit.text().strip()
        configuration.ilimodels = ';'.join(self.export_models_model.checked_models())
        configuration.base_configuration = self.base_configuration

        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue(
            'QgsProjectGenerator/ili2pg/xtffile_export', configuration.xtffile)
        settings.setValue('QgsProjectGenerator/importtype',
                          self.type_combo_box.currentData())

        if self.type_combo_box.currentData() in ['ili2pg', 'pg']:
            # PostgreSQL specific options
            settings.setValue(
                'QgsProjectGenerator/ili2pg/host', configuration.dbhost)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/port', configuration.dbport)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/user', configuration.dbusr)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/database', configuration.database)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/schema', configuration.dbschema)
            settings.setValue(
                'QgsProjectGenerator/ili2pg/password', configuration.dbpwd)
        elif self.type_combo_box.currentData() in ['ili2gpkg', 'gpkg']:
            settings.setValue(
                'QgsProjectGenerator/ili2gpkg/dbfile', configuration.dbfile)

    def restore_configuration(self):
        settings = QSettings()

        self.xtf_file_line_edit.setText(settings.value(
            'QgsProjectGenerator/ili2pg/xtffile_export'))
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

        mode = settings.value('QgsProjectGenerator/importtype', 'pg')
        mode = 'pg' if mode == 'ili2pg' else mode
        mode = 'gpkg' if mode == 'ili2gpkg' else mode
        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self.type_changed()

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
        if self.type_combo_box.currentData() == 'pg':
            self.pg_config.show()
            self.gpkg_config.hide()
        elif self.type_combo_box.currentData() == 'gpkg':
            self.pg_config.hide()
            self.gpkg_config.show()

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgsProjectGenerator/ili2db')
                self.base_configuration.save(settings)
        else:
            QDesktopServices.openUrl(link)

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/projectgenerator/docs/{}/user-guide.html#export-an-interlis-transfer-file-xtf".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/projectgenerator/docs/user-guide.html#export-an-interlis-transfer-file-xtf")

    def xtf_browser_opened_to_true(self):
        """
        Slot. Sets a flag to true to eventually avoid asking a user whether to overwrite a file.
        """
        self.xtf_browser_was_opened = True

    def xtf_browser_opened_to_false(self):
        """
        Slot. Sets a flag to false to eventually ask a user whether to overwrite a file.
        """
        self.xtf_browser_was_opened = False

    def advance_progress_bar_by_text(self, text):
        if text.strip() == 'Info: compile models…':
            self.progress_bar.setValue(50)
        elif text.strip() == 'Info: create table structure…':
            self.progress_bar.setValue(75)
