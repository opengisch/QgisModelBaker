"""
/***************************************************************************
                              -------------------
        begin                : 2022-08-01
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
        email                : david at opengis ch
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
import tempfile
from enum import IntEnum

from qgis.core import Qgis, QgsMapLayer, QgsMessageLog, QgsProject
from qgis.PyQt.QtCore import QAbstractItemModel, QModelIndex, Qt
from qgis.PyQt.QtWidgets import QHeaderView, QTableView, QWizardPage

from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils import db_utils
from QgisModelBaker.libs.modelbaker.utils.ili2db_utils import Ili2DbUtils
from QgisModelBaker.libs.modelbaker.utils.qt_utils import make_file_selector
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("topping_wizard/ili2dbsettings.ui")


class ParametersModel(QAbstractItemModel):
    """
    ItemModel providing the ili2db setting properties.
    """

    class Columns(IntEnum):
        NAME = 0
        VALUE = 1

    def __init__(self, parameters):
        super().__init__()
        self.parameters = parameters

    def columnCount(self, parent):
        return len(ParametersModel.Columns)

    def rowCount(self, parent):
        return len(self.parameters)

    def flags(self, index):
        return Qt.ItemIsEnabled

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        """
        default override
        """
        return super().createIndex(row, column, parent)

    def parent(self, index):
        """
        default override
        """
        return index

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == ParametersModel.Columns.NAME:
                return self.tr("Name")
            if section == ParametersModel.Columns.VALUE:
                return self.tr("Value")

    def data(self, index, role):
        if role == int(Qt.DisplayRole) or role == int(Qt.EditRole):
            if index.column() == ParametersModel.Columns.NAME:
                return list(self.parameters.keys())[index.row()]
            if index.column() == ParametersModel.Columns.VALUE:
                key = list(self.parameters.keys())[index.row()]
                return self.parameters.get(key, "")
        return None

    # this is unusual that it's not first data and then role (could be changed)
    def setData(self, index, role, data):
        if role == int(Qt.EditRole):
            if index.column() == ParametersModel.Columns.NAME:
                key = list(self.parameters.keys())[index.row()]
                self.parameters[key] = self.parameters.pop(key)
                self.dataChanged.emit(index, index)
            if index.column() == ParametersModel.Columns.VALUE:
                key = list(self.parameters.keys())[index.row()]
                self.parameters[key] = data
                self.dataChanged.emit(index, index)

    def refresh_model(self, parameters):
        self.beginResetModel()
        self.parameters = parameters
        self.endResetModel()


class Ili2dbSettingsPage(QWizardPage, PAGE_UI):

    ValidExtensions = ["toml", "TOML", "ini", "INI"]
    SQLValidExtensions = ["sql", "SQL"]

    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)

        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.setTitle(title)

        self.schema_combobox.currentIndexChanged.connect(self._schema_changed)

        self.parameters_model = ParametersModel(
            self.topping_wizard.topping.metaconfig.ili2db_settings.parameters
        )
        self.parameters_table_view.setModel(self.parameters_model)
        self.parameters_table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.parameters_table_view.setSelectionMode(QTableView.SingleSelection)

        self.toml_file_browse_button.clicked.connect(
            make_file_selector(
                self.toml_file_line_edit,
                title=self.tr("Open Extra Meta Attribute File (*.toml *.ini)"),
                file_filter=self.tr(
                    "Extra Meta Attribute File (*.toml *.TOML *.ini *.INI)"
                ),
            )
        )
        self.pre_script_file_browse_button.clicked.connect(
            make_file_selector(
                self.pre_script_file_line_edit,
                title=self.tr("SQL script to run before (*.sql)"),
                file_filter=self.tr("SQL script to run before (*.sql *.SQL)"),
            )
        )
        self.post_script_file_browse_button.clicked.connect(
            make_file_selector(
                self.post_script_file_line_edit,
                title=self.tr("SQL script to run after (*.sql)"),
                file_filter=self.tr("SQL script to run after (*.sql *.SQL)"),
            )
        )
        self.validators = gui_utils.Validators()
        self.file_validator = gui_utils.FileValidator(
            pattern=["*." + ext for ext in self.ValidExtensions], allow_empty=True
        )
        self.toml_file_line_edit.setValidator(self.file_validator)

        self.sql_file_validator = gui_utils.FileValidator(
            pattern=["*." + ext for ext in self.SQLValidExtensions], allow_empty=True
        )
        self.pre_script_file_line_edit.setValidator(self.sql_file_validator)
        self.post_script_file_line_edit.setValidator(self.sql_file_validator)

        self.toml_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.toml_file_line_edit.textChanged.emit(self.toml_file_line_edit.text())
        self.pre_script_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.pre_script_file_line_edit.textChanged.emit(
            self.pre_script_file_line_edit.text()
        )
        self.post_script_file_line_edit.textChanged.connect(
            self.validators.validate_line_edits
        )
        self.post_script_file_line_edit.textChanged.emit(
            self.post_script_file_line_edit.text()
        )

    def initializePage(self) -> None:
        self._refresh_combobox()
        self.pre_script_file_line_edit.setText(
            self.topping_wizard.topping.metaconfig.ili2db_settings.prescript_path
        )
        self.post_script_file_line_edit.setText(
            self.topping_wizard.topping.metaconfig.ili2db_settings.postscript_path
        )
        self.toml_file_line_edit.setText(
            self.topping_wizard.topping.metaconfig.ili2db_settings.metaattr_path
        )
        return super().initializePage()

    def validatePage(self) -> bool:
        self.topping_wizard.topping.metaconfig.ili2db_settings.prescript_path = (
            self.pre_script_file_line_edit.text()
        )
        self.topping_wizard.topping.metaconfig.ili2db_settings.postscript_path = (
            self.post_script_file_line_edit.text()
        )
        self.topping_wizard.topping.metaconfig.ili2db_settings.metaattr_path = (
            self.toml_file_line_edit.text()
        )
        self.topping_wizard.topping.metaconfig.metaconfigparamsonly = (
            self.metaconfigparamsonly_checkbox.isChecked()
        )
        self.topping_wizard.log_panel.print_info(
            self.tr(
                "Chosen ili2db settings from: {schema}".format(
                    schema=self.schema_combobox.currentText()
                )
            ),
            gui_utils.LogLevel.SUCCESS,
        )
        if self.topping_wizard.topping.metaconfig.ili2db_settings.prescript_path:
            self.topping_wizard.log_panel.print_info(
                self.tr(
                    "Pre-script: {path}".format(
                        path=self.topping_wizard.topping.metaconfig.ili2db_settings.prescript_path
                    )
                ),
                gui_utils.LogLevel.SUCCESS,
            )
        if self.topping_wizard.topping.metaconfig.ili2db_settings.postscript_path:
            self.topping_wizard.log_panel.print_info(
                self.tr(
                    "Post-script: {path}".format(
                        path=self.topping_wizard.topping.metaconfig.ili2db_settings.postscript_path
                    )
                ),
                gui_utils.LogLevel.SUCCESS,
            )
        if self.topping_wizard.topping.metaconfig.ili2db_settings.metaattr_path:
            self.topping_wizard.log_panel.print_info(
                self.tr(
                    "Extra Meta Attribute File: {path}".format(
                        path=self.topping_wizard.topping.metaconfig.ili2db_settings.metaattr_path
                    )
                ),
                gui_utils.LogLevel.SUCCESS,
            )
        if self.topping_wizard.topping.metaconfig.metaconfigparamsonly:
            self.topping_wizard.log_panel.print_info(
                self.tr(
                    "This metaconfiguration will be passed without any additional settings on import made by Model Baker (except models and on disable constraint run): qgis.modelbaker.metaConfigParamsOnly = true"
                ),
                gui_utils.LogLevel.SUCCESS,
            )
        return super().validatePage()

    def _refresh_combobox(self):
        self.schema_combobox.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                source_provider = layer.dataProvider()
                if not source_provider:
                    continue
                schema_identificator = (
                    db_utils.get_schema_identificator_from_sourceprovider(
                        source_provider
                    )
                )
                if (
                    not schema_identificator
                    or self.schema_combobox.findText(schema_identificator) > -1
                ):
                    continue

                configuration = Ili2DbCommandConfiguration()
                valid, mode = db_utils.get_configuration_from_sourceprovider(
                    source_provider, configuration
                )
                if valid and mode:
                    db_connector = db_utils.get_db_connector(configuration)
                    # only load it when it exists and metadata there (contains interlis data)
                    if (
                        db_connector
                        and db_connector.db_or_schema_exists()
                        and db_connector.metadata_exists()
                    ):
                        self.schema_combobox.addItem(
                            schema_identificator, configuration
                        )

        self.schema_combobox.addItem(
            self.tr("Not loading ili2db settings from schema"), None
        )

    def _schema_changed(self):
        configuration = self.schema_combobox.currentData()
        parsed_from_file = False
        if configuration:
            _, tmp_ini_file = tempfile.mkstemp(".ini")

            ili2db_utils = Ili2DbUtils()
            ili2db_utils.log_on_error.connect(self._log_on_export_metagonfig_error)
            res, msg = ili2db_utils.export_metaconfig(tmp_ini_file, configuration)
            if res:
                parsed_from_file = self.topping_wizard.topping.metaconfig.ili2db_settings.parse_parameters_from_ini_file(
                    tmp_ini_file
                )
        if not parsed_from_file:
            self.topping_wizard.topping.metaconfig.ili2db_settings.parameters = {}
        self.parameters_model.refresh_model(
            self.topping_wizard.topping.metaconfig.ili2db_settings.parameters
        )

    def _log_on_export_metagonfig_error(self, log):
        QgsMessageLog.logMessage(log, self.tr("Export metaConfig"), Qgis.Critical)
