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

from qgis.PyQt.QtCore import QLocale, QSettings, Qt
from qgis.PyQt.QtWidgets import QDialog, QTableWidgetItem

from QgisModelBaker.gui.custom_model_dir import CustomModelDirDialog
from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    ExportConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils import qt_utils
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import DropMode

DIALOG_UI = gui_utils.get_ui_class("options.ui")


class OptionsDialog(QDialog, DIALOG_UI):
    def __init__(self, configuration, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.configuration = configuration
        self.db_simple_factory = DbSimpleFactory()

        self.pg_user_line_edit.setText(configuration.super_pg_user)
        self.pg_password_line_edit.setText(configuration.super_pg_password)

        self.pg_param_map = configuration.dbparam_map
        self.pg_dbparam_button.clicked.connect(self._dbparams_open)

        self.custom_model_directories_line_edit.setText(
            configuration.custom_model_directories
        )
        self.custom_model_directories_box.setChecked(
            configuration.custom_model_directories_enabled
        )
        self.java_path_line_edit.setText(configuration.java_path)
        self.java_path_search_button.clicked.connect(
            qt_utils.make_file_selector(
                self.java_path_line_edit,
                self.tr("Select Java application"),
                self.tr("java (*)"),
            )
        )
        self.java_path_line_edit.setValidator(
            gui_utils.FileValidator(is_executable=True, allow_empty=True)
        )
        self.validators = gui_utils.Validators()
        self.java_path_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.ili2db_logfile_path.setText(configuration.logfile_path)
        self.ili2db_logfile_search_button.clicked.connect(
            qt_utils.make_save_file_selector(
                self.ili2db_logfile_path,
                self.tr("Select log file"),
                self.tr("Text files (*.txt)"),
            )
        )
        self.ili2db_enable_debugging.setChecked(self.configuration.debugging_enabled)
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.helpRequested.connect(self.help_requested)
        self.custom_models_dir_button.clicked.connect(self.show_custom_model_dir)

        for db_id in self.db_simple_factory.get_db_list(False):
            db_id |= DbIliMode.ili
            self.ili2db_tool_combobox.addItem(db_id.name, db_id)

        self.ili2db_action_combobox.addItem(self.tr("Schema Import"), "schemaimport")
        self.ili2db_action_combobox.addItem(self.tr("Data Import"), "import")
        self.ili2db_action_combobox.addItem(self.tr("Data Export"), "export")

        self.ili2db_tool_combobox.currentIndexChanged.connect(
            self.ili2db_command_reload
        )
        self.ili2db_action_combobox.currentIndexChanged.connect(
            self.ili2db_command_reload
        )

        self.ili2db_command_reload()

        settings = QSettings()
        drop_mode = DropMode[
            settings.value("QgisModelBaker/drop_mode", DropMode.ASK.name, str)
        ]
        self.chk_dontask_to_handle_dropped_files.setEnabled(drop_mode != DropMode.ASK)
        self.chk_dontask_to_handle_dropped_files.setChecked(drop_mode != DropMode.ASK)

        self.chk_open_always_wizard_to_handle_dropped_files.setChecked(
            settings.value("QgisModelBaker/open_wizard_always", False, bool)
        )

    def accepted(self):
        self.configuration.custom_model_directories = (
            self.custom_model_directories_line_edit.text()
        )
        self.configuration.custom_model_directories_enabled = (
            self.custom_model_directories_box.isChecked()
        )
        self.configuration.java_path = self.java_path_line_edit.text().strip()
        self.configuration.logfile_path = self.ili2db_logfile_path.text()
        self.configuration.debugging_enabled = self.ili2db_enable_debugging.isChecked()

        self.configuration.super_pg_user = self.pg_user_line_edit.text()
        self.configuration.super_pg_password = self.pg_password_line_edit.text()

        self.configuration.dbparam_map = self.pg_param_map

        settings = QSettings()
        if not self.chk_dontask_to_handle_dropped_files.isChecked():
            settings.setValue("QgisModelBaker/drop_mode", DropMode.ASK.name)

        settings.setValue(
            "QgisModelBaker/open_wizard_always",
            self.chk_open_always_wizard_to_handle_dropped_files.isChecked(),
        )

    def _dbparams_open(self):
        db_params_dialog = DbParamsDialog(self, self.pg_param_map)
        if db_params_dialog.exec() == QDialog.DialogCode.Accepted:
            self.pg_param_map = db_params_dialog.param_map

    def show_custom_model_dir(self):
        dlg = CustomModelDirDialog(self.custom_model_directories_line_edit.text(), self)
        dlg.exec()

    def help_requested(self):
        os_language = QLocale(QSettings().value("locale/userLocale")).name()[:2]
        if os_language in ["fr", "it", "de"]:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/{}/user_guide/plugin_configuration".format(
                    os_language
                )
            )
        else:
            webbrowser.open(
                "https://opengisch.github.io/QgisModelBaker/user_guide/plugin_configuration"
            )

    def ili2db_command_reload(self):
        config = None

        if self.ili2db_action_combobox.currentData() == "schemaimport":
            config = SchemaImportConfiguration()
            config.create_basket_col = True
        elif self.ili2db_action_combobox.currentData() == "import":
            config = ImportDataConfiguration()
        elif self.ili2db_action_combobox.currentData() == "export":
            config = ExportConfiguration()

        executable = "java -jar {}.jar".format(
            self.ili2db_tool_combobox.currentData().name
        )
        command = "\n  ".join([executable] + config.to_ili2db_args())

        self.ili2db_options_textedit.setText(command)


DIALOG_UI = gui_utils.get_ui_class("dbparam_map.ui")


class DbParamsDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None, param_map={}):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.param_map = param_map

        self.mappingtable.horizontalHeader().setSectionsClickable(True)
        self.mappingtable.setSortingEnabled(True)

        self.init()
        self.buttonBox.accepted.connect(self.accepted)
        self.mappingtable.cellChanged.connect(self._cell_changed)

    def init(self):
        """
        Reads content from param_map
        """
        for key in self.param_map.keys():
            row = self.mappingtable.rowCount()
            self.mappingtable.insertRow(row)
            key_item = QTableWidgetItem()
            key_item.setData(Qt.ItemDataRole.DisplayRole, key)
            value_item = QTableWidgetItem()
            value_item.setData(Qt.ItemDataRole.DisplayRole, self.param_map[key])
            self.mappingtable.setItem(row, 0, key_item)
            self.mappingtable.setItem(row, 1, value_item)
        self.mappingtable.insertRow(self.mappingtable.rowCount())

    def accepted(self):
        """
        Stores content to param_map
        """
        self.param_map = {}
        for row in range(self.mappingtable.rowCount()):
            key_item = self.mappingtable.item(row, 0)
            if key_item and len(str(key_item.data(Qt.ItemDataRole.DisplayRole))) > 0:
                value_item = self.mappingtable.item(row, 1)
                if (
                    value_item
                    and len(str(value_item.data(Qt.ItemDataRole.DisplayRole))) > 0
                ):
                    self.param_map[
                        str(key_item.data(Qt.ItemDataRole.DisplayRole))
                    ] = str(value_item.data(Qt.ItemDataRole.DisplayRole))

    def _cell_changed(self, row, column):
        """
        If one of the cells in this row has content and is the last row, add an additional row.
        If none of the cells in this row has context and it's the second last row, remove the last row.
        """
        key_item = self.mappingtable.item(row, 0)
        value_item = self.mappingtable.item(row, 1)
        # if we did something the second last row and it's empty (means we cleared it), we remove the empty row at the end.
        if row == self.mappingtable.rowCount() - 2 and not (
            key_item
            and len(str(key_item.data(Qt.ItemDataRole.DisplayRole))) > 0
            or value_item
            and len(str(value_item.data(Qt.ItemDataRole.DisplayRole))) > 0
        ):
            self.mappingtable.removeRow(row + 1)
        # if we did something in the last row, and it's not empty, we add a fresh empty row at the end.
        elif row == self.mappingtable.rowCount() - 1 and (
            key_item
            and len(str(key_item.data(Qt.ItemDataRole.DisplayRole))) > 0
            or value_item
            and len(str(value_item.data(Qt.ItemDataRole.DisplayRole))) > 0
        ):
            self.mappingtable.insertRow(row + 1)
