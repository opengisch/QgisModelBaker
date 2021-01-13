# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 6.6.2017
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

from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DropMode
from QgisModelBaker.libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libili2db.ili2dbconfig import SchemaImportConfiguration, ImportDataConfiguration, \
    ExportConfiguration
from QgisModelBaker.utils import get_ui_class
from QgisModelBaker.utils import qt_utils
from QgisModelBaker.gui.custom_model_dir import CustomModelDirDialog
from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QListView
from qgis.PyQt.QtCore import QLocale, QSettings, pyqtSignal, pyqtSlot, Qt, QModelIndex
from QgisModelBaker.utils.qt_utils import FileValidator, Validators

DIALOG_UI = get_ui_class('options.ui')


class OptionsDialog(QDialog, DIALOG_UI):

    def __init__(self, configuration, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.configuration = configuration
        self.db_simple_factory = DbSimpleFactory()

        self.pg_user_line_edit.setText(configuration.super_pg_user)
        self.pg_password_line_edit.setText(configuration.super_pg_password)

        self.custom_model_directories_line_edit.setText(
            configuration.custom_model_directories)
        self.custom_model_directories_box.setChecked(
            configuration.custom_model_directories_enabled)
        self.java_path_line_edit.setText(configuration.java_path)
        self.java_path_search_button.clicked.connect(qt_utils.make_file_selector(
            self.java_path_line_edit, self.tr('Select Java application'), self.tr('java (*)')))
        self.java_path_line_edit.setValidator(
            FileValidator(is_executable=True, allow_empty=True))
        self.validators = Validators()
        self.java_path_line_edit.textChanged.connect(
            self.validators.validate_line_edits)
        self.ili2db_logfile_path.setText(configuration.logfile_path)
        self.ili2db_logfile_search_button.clicked.connect(qt_utils.make_save_file_selector(
            self.ili2db_logfile_path, self.tr('Select log file'), self.tr('Text files (*.txt)')))
        self.ili2db_enable_debugging.setChecked(
            self.configuration.debugging_enabled)
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.custom_models_dir_button.clicked.connect(
            self.show_custom_model_dir)

        for db_id in self.db_simple_factory.get_db_list(False):
            db_id |= DbIliMode.ili
            self.ili2db_tool_combobox.addItem(db_id.name, db_id)

        self.ili2db_action_combobox.addItem(
            self.tr('Schema Import'), 'schemaimport')
        self.ili2db_action_combobox.addItem(self.tr('Data Import'), 'import')
        self.ili2db_action_combobox.addItem(self.tr('Data Export'), 'export')

        self.ili2db_tool_combobox.currentIndexChanged.connect(
            self.ili2db_command_reload)
        self.ili2db_action_combobox.currentIndexChanged.connect(
            self.ili2db_command_reload)

        self.ili2db_command_reload()

        settings = QSettings()
        drop_mode = DropMode(settings.value('QgisModelBaker/drop_mode', 3, int))
        self.chk_dontask_to_handle_dropped_files.setEnabled(drop_mode != DropMode.ask)
        self.chk_dontask_to_handle_dropped_files.setChecked(drop_mode != DropMode.ask)

    def accepted(self):
        self.configuration.custom_model_directories = self.custom_model_directories_line_edit.text()
        self.configuration.custom_model_directories_enabled = self.custom_model_directories_box.isChecked()
        self.configuration.java_path = self.java_path_line_edit.text().strip()
        self.configuration.logfile_path = self.ili2db_logfile_path.text()
        self.configuration.debugging_enabled = self.ili2db_enable_debugging.isChecked()

        self.configuration.super_pg_user = self.pg_user_line_edit.text()
        self.configuration.super_pg_password = self.pg_password_line_edit.text()

        settings = QSettings()
        if not self.chk_dontask_to_handle_dropped_files.isChecked():
            settings.setValue('QgisModelBaker/drop_mode', DropMode.ask.value)

    def show_custom_model_dir(self):
        dlg = CustomModelDirDialog(
            self.custom_model_directories_line_edit.text(), self)
        dlg.exec_()

    def help_requested(self):
        os_language = QLocale(QSettings().value(
            'locale/userLocale')).name()[:2]
        if os_language in ['es', 'de']:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/{}/user-guide.html#plugin-configuration".format(os_language))
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/docs/user-guide.html#plugin-configuration")

    def ili2db_command_reload(self):
        config = None

        if self.ili2db_action_combobox.currentData() == 'schemaimport':
            config = SchemaImportConfiguration()
        elif self.ili2db_action_combobox.currentData() == 'import':
            config = ImportDataConfiguration()
        elif self.ili2db_action_combobox.currentData() == 'export':
            config = ExportConfiguration()

        executable = 'java -jar {}.jar'.format(
            self.ili2db_tool_combobox.currentData().name)
        command = '\n  '.join([executable] + config.to_ili2db_args())

        self.ili2db_options_textedit.setText(command)


class CompletionLineEdit(QLineEdit):

    punched = pyqtSignal()

    def __init__(self, parent=None):
        super(CompletionLineEdit, self).__init__(parent)
        self.readyToEdit = True

    def focusInEvent(self, e):
        super(CompletionLineEdit, self).focusInEvent(e)
        self.punched.emit()

    def mouseReleaseEvent(self, e):
        super(CompletionLineEdit, self).mouseReleaseEvent(e)
        self.punched.emit()


class ModelListView(QListView):

    space_pressed = pyqtSignal(QModelIndex)

    def __init__(self, parent=None):
        super(QListView, self).__init__(parent)
        self.space_pressed.connect(self.update)

    #to act when space is pressed
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            _selected_indexes = self.selectedIndexes()
            self.space_pressed.emit(_selected_indexes[0])
        super(ModelListView, self).keyPressEvent(e)
