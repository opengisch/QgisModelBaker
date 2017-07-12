# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 30/05/17
        git sha              : :%H$
        copyright            : (C) 2017 by Germán Carrillo
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

from projectgenerator.gui.options import OptionsDialog
from projectgenerator.libili2pg.iliexporter import JavaNotFoundError
from projectgenerator.libili2pg.ilicache import IliCache
from projectgenerator.utils.qt_utils import make_save_file_selector, Validators, make_folder_selector
from qgis.PyQt.QtGui import QColor, QDesktopServices, QFont, QRegExpValidator
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QApplication, QCompleter
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QRegExp, Qt
from qgis.core import QgsProject
from ..utils import get_ui_class
from ..libili2pg import iliexporter, ili2pg_config

DIALOG_UI = get_ui_class('export.ui')


class ExportDialog(QDialog, DIALOG_UI):
    def __init__(self, base_config, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.clear()
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.addButton(self.tr('Export'), QDialogButtonBox.AcceptRole)
        self.xtf_file_browse_button.clicked.connect(make_save_file_selector(self.xtf_file_line_edit, title=self.tr('Save in XTF Transfer File'), file_filter=self.tr('XTF Transfer File (*.xtf)')))

        self.base_configuration = base_config
        self.restore_configuration()

        self.validators = Validators()
        regexp = QRegExp("[a-zA-Z_0-9]+") # Non empty string
        validator = QRegExpValidator(regexp)

        self.pg_host_line_edit.setValidator(validator)
        self.pg_database_line_edit.setValidator(validator)
        self.pg_user_line_edit.setValidator(validator)

        self.pg_host_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_host_line_edit.textChanged.emit(self.pg_host_line_edit.text())
        self.pg_database_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_database_line_edit.textChanged.emit(self.pg_database_line_edit.text())
        self.pg_user_line_edit.textChanged.connect(self.validators.validate_line_edits)
        self.pg_user_line_edit.textChanged.emit(self.pg_user_line_edit.text())
        self.ilicache = IliCache(base_config)
        self.ilicache.models_changed.connect(self.update_models_completer)
        self.ilicache.refresh()

    def accepted(self):
        configuration = self.updated_configuration()

        QApplication.setOverrideCursor( Qt.WaitCursor )
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()

        exporter = iliexporter.Exporter()

        exporter.configuration = configuration

        self.save_configuration(configuration)

        exporter.stdout.connect(self.print_info)
        exporter.stderr.connect(self.on_stderr)
        exporter.process_started.connect(self.on_process_started)
        exporter.process_finished.connect(self.on_process_finished)

        try:
            if exporter.run() != iliexporter.Exporter.SUCCESS:
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
        self.disable()
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.clear()
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        self.txtStdout.setTextColor(QColor('#777777'))
        self.txtStdout.append('Finished ({})'.format(exit_code))
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
        configuration = ili2pg_config.ExportConfiguration()

        configuration.host = self.pg_host_line_edit.text().strip()
        configuration.user = self.pg_user_line_edit.text().strip()
        configuration.database = self.pg_database_line_edit.text().strip()
        configuration.schema = self.pg_schema_line_edit.text().strip()
        configuration.password = self.pg_password_line_edit.text()
        configuration.xtffile = self.xtf_file_line_edit.text().strip()
        configuration.ilimodels = self.ili_models_line_edit.text().strip()
        configuration.java_path = QSettings().value('QgsProjectGenerator/java_path', '')
        configuration.base_configuration = self.base_configuration

        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgsProjectGenerator/ili2pg/xtffile', configuration.xtffile)
        settings.setValue('QgsProjectGenerator/ili2pg/host', configuration.host)
        settings.setValue('QgsProjectGenerator/ili2pg/user', configuration.user)
        settings.setValue('QgsProjectGenerator/ili2pg/database', configuration.database)
        settings.setValue('QgsProjectGenerator/ili2pg/schema', configuration.schema)
        settings.setValue('QgsProjectGenerator/ili2pg/password', configuration.password)

    def restore_configuration(self):
        settings = QSettings()

        self.xtf_file_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/xtffile'))
        self.pg_host_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/host', 'localhost'))
        self.pg_user_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/user'))
        self.pg_database_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/database'))
        self.pg_schema_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/schema'))
        self.pg_password_line_edit.setText(settings.value('QgsProjectGenerator/ili2pg/password'))

    def disable(self):
        self.pg_config.setEnabled(False)
        self.ili_config.setEnabled(False)
        self.buttonBox.setEnabled(False)

    def enable(self):
        self.pg_config.setEnabled(True)
        self.ili_config.setEnabled(True)
        self.buttonBox.setEnabled(True)

    def link_activated(self, link):
        if link.url() == '#configure':
            cfg = OptionsDialog(self.base_configuration)
            if cfg.exec_():
                settings = QSettings()
                settings.beginGroup('QgsProjectGenerator/ili2db')
                self.base_configuration.save(settings)

        else:
            QDesktopServices.openUrl(link)

    def update_models_completer(self):
        completer = QCompleter(self.ilicache.model_names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ili_models_line_edit.setCompleter(completer)
