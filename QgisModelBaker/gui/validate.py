"""
/***************************************************************************
                              -------------------
        begin                : 11/11/21
        git sha              : :%H$
        copyright            : (C) 2021 by Dave Signer
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
import logging
import os

from PyQt5.QtGui import QColor, QGuiApplication
from qgis.core import (
    QgsApplication,
    QgsExpressionContextUtils,
    QgsGeometry,
    QgsMapLayer,
    QgsPointXY,
    QgsProject,
    QgsRectangle,
)
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QStandardPaths, Qt, QTimer
from qgis.PyQt.QtWidgets import (
    QAction,
    QDockWidget,
    QFileDialog,
    QHeaderView,
    QMenu,
    QMessageBox,
)

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.export_models_panel import ExportModelsPanel
from QgisModelBaker.gui.panel.filter_data_panel import FilterDataPanel
from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.iliwrapper import ilivalidator
from QgisModelBaker.libs.modelbaker.iliwrapper.globals import DbIliMode
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import ValidateConfiguration
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbutils import JavaNotFoundError
from QgisModelBaker.libs.modelbaker.iliwrapper.ilivalidator import ValidationResultModel
from QgisModelBaker.libs.modelbaker.utils.qt_utils import OverrideCursor
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import (
    SchemaBasketsModel,
    SchemaDataFilterMode,
    SchemaDatasetsModel,
    SchemaModelsModel,
)

DIALOG_UI = gui_utils.get_ui_class("validator.ui")


# validate tools
class ValidationResultTableModel(ValidationResultModel):
    """
    Model providing the data of the parsed xtf file to the defined columns for the table view use.
    """

    def __init__(self, roles):
        super().__init__()
        self.roles = roles
        self.setColumnCount(len(self.roles))
        self.setHorizontalHeaderLabels([role.name for role in self.roles])

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        item = self.item(index.row(), 0)
        if item:
            if role == Qt.DisplayRole:
                return item.data(int(self.roles[index.column()]))
            if role == Qt.DecorationRole:
                return (
                    QColor(gui_utils.SUCCESS_COLOR)
                    if item.data(int(ValidationResultModel.Roles.FIXED))
                    else QColor(gui_utils.ERROR_COLOR)
                )
            if role == Qt.ToolTipRole:
                tooltip_text = "{type} at {tid} in {object}".format(
                    type=item.data(int(ValidationResultModel.Roles.TYPE)),
                    object=item.data(int(ValidationResultModel.Roles.OBJ_TAG)),
                    tid=item.data(int(ValidationResultModel.Roles.TID)),
                )
                return tooltip_text
            return item.data(role)

    def setFixed(self, index):
        item = self.item(index.row(), 0)
        if item:
            item.setData(
                not item.data(int(ValidationResultModel.Roles.FIXED)),
                int(ValidationResultModel.Roles.FIXED),
            )


class ValidateDock(QDockWidget, DIALOG_UI):
    class SchemaValidation:
        """
        A "validation" should be keeped on layer change and "reused" if it's the same database schema of the layer.
        """

        def __init__(self):
            self.models_model = SchemaModelsModel()
            self.datasets_model = SchemaDatasetsModel()
            self.baskets_model = SchemaBasketsModel()
            self.export_models_model = SchemaModelsModel()
            self.result_model = None

    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.base_config = base_config
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)

        self.schema_validations = {}
        self.requested_roles = [ValidationResultModel.Roles.MESSAGE]

        self.current_configuration = ValidateConfiguration()
        self.current_configuration.base_configuration = self.base_config
        self.current_schema_identificator = ""
        self.current_models_model = SchemaModelsModel()
        self.current_datasets_model = SchemaDatasetsModel()
        self.current_baskets_model = SchemaBasketsModel()
        self.current_filter_mode = SchemaDataFilterMode.NO_FILTER
        self.current_export_models_model = SchemaModelsModel()
        self.current_export_models_active = False

        self.filter_data_panel = FilterDataPanel(self)
        self.filter_data_panel.setMaximumHeight(self.fontMetrics().lineSpacing() * 10)
        self.filter_layout.addWidget(self.filter_data_panel)

        self.export_models_panel = ExportModelsPanel(self)
        self.export_models_panel.setMaximumHeight(self.fontMetrics().lineSpacing() * 10)
        self.export_models_layout.addWidget(self.export_models_panel)
        self._reset_gui()

        self.run_button.clicked.connect(self._run)
        self.visibilityChanged.connect(self._visibility_changed)

        self.result_table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.result_table_view.customContextMenuRequested.connect(
            self._table_context_menu_requested
        )
        self.result_table_view.clicked.connect(self._table_clicked)

        self.flash_button.setIcon(
            QgsApplication.getThemeIcon("/mActionHighlightFeature.svg")
        )
        self.auto_pan_button.setIcon(QgsApplication.getThemeIcon("/mActionPanTo.svg"))
        self.auto_zoom_button.setIcon(QgsApplication.getThemeIcon("/mActionZoomTo.svg"))

        self.auto_pan_button.clicked.connect(self._auto_pan_button_clicked)
        self.auto_zoom_button.clicked.connect(self._auto_zoom_button_clicked)

        save_config_file_action = QAction(
            QgsApplication.getThemeIcon("/mActionFileSave.svg"),
            self.tr("Save config file to project..."),
            self,
        )
        save_config_file_action.triggered.connect(self._save_config_file)
        self.config_file_tool_button.addAction(save_config_file_action)
        load_config_file_action = QAction(
            QgsApplication.getThemeIcon("/mActionFileOpen.svg"),
            self.tr("Load config file from project..."),
            self,
        )
        load_config_file_action.triggered.connect(self._load_config_file)
        self.config_file_tool_button.addAction(load_config_file_action)
        self.config_file_tool_button.clicked.connect(self._select_config_file)

    def _reset_current_values(self):
        self.current_configuration = ValidateConfiguration()
        self.current_configuration.base_configuration = self.base_config
        self.current_schema_identificator = ""
        self.current_models_model = SchemaModelsModel()
        self.current_datasets_model = SchemaDatasetsModel()
        self.current_baskets_model = SchemaBasketsModel()
        self.current_filter_mode = SchemaDataFilterMode.NO_FILTER
        self.current_export_models_model = SchemaModelsModel()
        self.current_export_models_active = False
        self.config_file_line_edit.clear()

    def _reset_gui(self):
        self._reset_current_values()
        self.info_label.setText("")
        self.progress_bar.setTextVisible(False)
        self._set_count_label(0)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.result_table_view.setModel(
            ValidationResultTableModel(self.requested_roles)
        )
        self.result_table_view.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.result_table_view.verticalHeader().hide()
        self.result_table_view.horizontalHeader().hide()
        self.result_table_view.setSelectionBehavior(QHeaderView.SelectRows)
        self.result_table_view.setSelectionMode(QHeaderView.SingleSelection)

        self.setDisabled(True)

    def set_current_layer(self, layer):
        if self.isHidden():
            return

        if not layer or not layer.dataProvider() or not layer.dataProvider().isValid():
            self.setDisabled(True)
            return

        source_provider = layer.dataProvider()
        schema_identificator = db_utils.get_schema_identificator_from_sourceprovider(
            source_provider
        )
        if not schema_identificator:
            self.setDisabled(True)
            return
        if schema_identificator == self.current_schema_identificator:
            self.setEnabled(True)
            return

        self._reset_gui()

        self.current_schema_identificator = schema_identificator
        valid, mode = db_utils.get_configuration_from_sourceprovider(
            source_provider, self.current_configuration
        )
        if valid and mode:
            output_file_name = "{}.xtf".format(self.current_schema_identificator)
            self.current_configuration.xtflog = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                output_file_name,
            )
            self.current_configuration.xtffile = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                f"dataexport_{output_file_name}",
            )
            self.current_configuration.tool = mode
            if mode == DbIliMode.gpkg:
                self.info_label.setText(
                    self.tr(
                        "<html><head/><body><p>Datasource is the databasefile <i>{}</i></p></body></html>"
                    ).format(self.current_configuration.dbfile)
                )
            else:
                self.info_label.setText(
                    self.tr(
                        "<html><head/><body><p>Datasource is the schema <i>{}</i> at database <i>{}</i></p></body></html>"
                    ).format(
                        self.current_configuration.dbschema,
                        self.current_configuration.database,
                    )
                )

            self.current_configuration.with_exporttid = self._get_tid_handling()

            if self.schema_validations.get(self.current_schema_identificator):
                # don't set result if never got a validation (empty ValidateDock.SchemaValidation)
                if self.schema_validations[
                    self.current_schema_identificator
                ].result_model:
                    self._set_result(
                        self.schema_validations[
                            self.current_schema_identificator
                        ].result_model.valid
                    )
            else:
                self.schema_validations[
                    self.current_schema_identificator
                ] = ValidateDock.SchemaValidation()

            self._refresh_schemadata_models()
            self.current_models_model = self.schema_validations[
                self.current_schema_identificator
            ].models_model
            self.current_datasets_model = self.schema_validations[
                self.current_schema_identificator
            ].datasets_model
            self.current_baskets_model = self.schema_validations[
                self.current_schema_identificator
            ].baskets_model
            self.current_export_models_model = self.schema_validations[
                self.current_schema_identificator
            ].export_models_model

            self.filter_data_panel.setup_dialog(self._basket_handling())
            self.export_models_panel.setup_dialog(True)

            self._load_config_file()

            self.setDisabled(False)

    def _visibility_changed(self, visible):
        if visible:
            self.set_current_layer(self.iface.activeLayer())

    def _refresh_schemadata_models(self):
        db_connector = db_utils.get_db_connector(self.current_configuration)
        self.schema_validations[
            self.current_schema_identificator
        ].models_model.refresh_model([db_connector])
        self.schema_validations[
            self.current_schema_identificator
        ].datasets_model.refresh_model(db_connector)
        self.schema_validations[
            self.current_schema_identificator
        ].baskets_model.refresh_model(db_connector)
        self.schema_validations[
            self.current_schema_identificator
        ].export_models_model.refresh_model([db_connector])
        return

    def _basket_handling(self):
        db_connector = db_utils.get_db_connector(self.current_configuration)
        if db_connector:
            return db_connector.get_basket_handling()
        return False

    def _get_tid_handling(self):
        db_connector = db_utils.get_db_connector(self.current_configuration)
        if db_connector:
            return db_connector.get_tid_handling()
        return False

    def _run(self, edited_command=None):
        if self.iface.actionToggleEditing().isChecked():
            self.iface.actionToggleEditing().trigger()
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self._disable_controls(True)
        validator = ilivalidator.Validator()

        validator.stdout.connect(self._validator_stdout)
        validator.stderr.connect(self._validator_stderr)

        validator.tool = self.current_configuration.tool
        validator.configuration = self.current_configuration

        validator.configuration.ilimodels = ""
        validator.configuration.dataset = ""
        validator.configuration.baskets = []
        if self.current_filter_mode == SchemaDataFilterMode.MODEL:
            validator.configuration.ilimodels = ";".join(
                self.current_models_model.checked_entries()
            )
        elif self.current_filter_mode == SchemaDataFilterMode.DATASET:
            validator.configuration.dataset = ";".join(
                self.current_datasets_model.checked_entries()
            )
        elif self.current_filter_mode == SchemaDataFilterMode.BASKET:
            validator.configuration.baskets = (
                self.current_baskets_model.checked_entries()
            )
        else:
            validator.configuration.ilimodels = ";".join(
                self.current_models_model.stringList()
            )

        if self.current_export_models_active:
            validator.configuration.iliexportmodels = ";".join(
                self.current_export_models_model.checked_entries()
            )
        else:
            validator.configuration.iliexportmodels = ""

        validator.configuration.skip_geometry_errors = (
            self.skip_geometry_errors_check_box.isChecked()
        )
        validator.configuration.valid_config = self._absolute_path(
            self.config_file_line_edit.text()
        )
        print(validator.configuration.valid_config)

        self.progress_bar.setValue(20)
        validation_result_state = False
        with OverrideCursor(Qt.WaitCursor):
            try:
                self._validator_stdout(f"Run: {validator.command(True)}")
                validation_result_state = (
                    validator.run(edited_command) == ilivalidator.Validator.SUCCESS
                )
            except JavaNotFoundError as e:
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat(self.tr("Ili2db validation problems"))
                self.progress_bar.setTextVisible(True)
                self._disable_controls(False)

                QApplication.restoreOverrideCursor()
                QMessageBox.critical(
                    self, self.tr("Java not found error"), e.error_string
                )

                return

        self.progress_bar.setValue(50)
        result_model = ValidationResultTableModel(self.requested_roles)
        result_model.configuration = self.current_configuration
        result_model.valid = validation_result_state
        result_model.reload()

        self.progress_bar.setValue(75)
        self.schema_validations[
            self.current_schema_identificator
        ].result_model = result_model
        self._disable_controls(False)
        self._set_result(
            self.schema_validations[
                self.current_schema_identificator
            ].result_model.valid
        )
        self.progress_bar.setValue(100)

    def _set_result(self, valid):
        self.result_table_view.setModel(
            self.schema_validations[self.current_schema_identificator].result_model
        )

        self.result_table_view.setWordWrap(True)
        self.result_table_view.setTextElideMode(Qt.ElideLeft)
        self.result_table_view.resizeRowsToContents()

        if valid:
            self.progress_bar.setFormat(self.tr("Schema is valid"))
            self.setStyleSheet(gui_utils.SUCCESS_STYLE)
        else:
            self.progress_bar.setFormat(self.tr("Schema is not valid"))
            self.setStyleSheet(gui_utils.ERROR_STYLE)
        self.progress_bar.setTextVisible(True)
        self.result_table_view.setDisabled(valid)
        self._set_count_label(
            self.schema_validations[
                self.current_schema_identificator
            ].result_model.rowCount()
        )

    def _disable_controls(self, disable):
        self.run_button.setDisabled(disable)
        self.result_table_view.setDisabled(disable)

    def _set_count_label(self, count):
        text = self.tr("{} Errors".format(count))
        self.error_count_label.setText(text)

    def _table_context_menu_requested(self, pos):
        if not self.result_table_view.indexAt(pos).isValid():
            self.result_table_view.clearSelection()
            return
        selection_index = self.result_table_view.selectionModel().currentIndex()
        index = selection_index.sibling(selection_index.row(), selection_index.column())

        coord_x = index.data(int(ValidationResultModel.Roles.COORD_X))
        coord_y = index.data(int(ValidationResultModel.Roles.COORD_Y))
        t_ili_tid = index.data(int(ValidationResultModel.Roles.TID))
        id = index.data(int(ValidationResultModel.Roles.ID))
        text = index.data(Qt.DisplayRole)

        menu = QMenu()
        if coord_x and coord_y:
            action_zoom_to = QAction(
                QgsApplication.getThemeIcon("/mActionZoomToSelected.svg"),
                self.tr("Zoom to Coordinates"),
                self,
            )
            action_zoom_to.triggered.connect(
                lambda: self._zoom_to_coordinate(coord_x, coord_y)
            )
            menu.addAction(action_zoom_to)
        if t_ili_tid:
            action_open_form = QAction(
                QgsApplication.getThemeIcon("/mActionFormView.svg"),
                self.tr("Open in Feature Form"),
                self,
            )
            action_open_form.triggered.connect(lambda: self._open_form(t_ili_tid))
            menu.addAction(action_open_form)
            action_select_feature = QAction(
                QgsApplication.getThemeIcon("/mActionOpenTableSelected.svg"),
                self.tr("Select in Attribute Table"),
                self,
            )
            action_select_feature.triggered.connect(
                lambda: self._select_feature_in_attributetable(t_ili_tid)
            )
            menu.addAction(action_select_feature)
        if id:
            action_fix = QAction(
                self.tr("Set to unfixed")
                if index.data(int(ValidationResultModel.Roles.FIXED))
                else self.tr("Set to fixed"),
                self,
            )
            action_fix.triggered.connect(
                lambda: self.result_table_view.model().setFixed(index)
            )
            menu.addAction(action_fix)

            action_copy = QAction(
                QgsApplication.getThemeIcon("/mActionEditCopy.svg"),
                self.tr("Copy"),
                self,
            )
            action_copy.triggered.connect(
                lambda: QGuiApplication.clipboard().setText(text)
            )
            menu.addAction(action_copy)
        menu.exec_(self.result_table_view.mapToGlobal(pos))

    def _table_clicked(self, index):
        if not index.isValid():
            return

        coord_x = index.data(int(ValidationResultModel.Roles.COORD_X))
        coord_y = index.data(int(ValidationResultModel.Roles.COORD_Y))
        valid_coords = bool(coord_x and coord_y)

        t_ili_tid = index.data(int(ValidationResultModel.Roles.TID))
        layer, feature = self._get_feature_in_project(t_ili_tid)
        valid_feature = bool(layer and feature and feature.hasGeometry())

        if not valid_coords and not valid_feature:
            return

        if self.auto_pan_button.isChecked():
            if valid_coords:
                # prefering coordinates when having both
                QTimer.singleShot(1, lambda: self._pan_to_coordinate(coord_x, coord_y))

            else:
                # otherwise it has a valid feature
                QTimer.singleShot(
                    1,
                    lambda: self.iface.mapCanvas().panToFeatureIds(
                        layer, [feature.id()], False
                    ),
                )

        if self.auto_zoom_button.isChecked():
            if valid_coords:
                # prefering coordinates when having both
                QTimer.singleShot(
                    1,
                    lambda: self._set_extend(coord_x, coord_y),
                )
            else:
                # otherwise it has a valid feature
                QTimer.singleShot(
                    1,
                    lambda: self.iface.mapCanvas().zoomToFeatureIds(
                        layer, [feature.id()]
                    ),
                )

        if self.flash_button.isChecked():
            if valid_coords:
                QTimer.singleShot(
                    1,
                    lambda: self.iface.mapCanvas().flashGeometries(
                        [
                            QgsGeometry.fromPointXY(
                                QgsPointXY(float(coord_x), float(coord_y))
                            )
                        ]
                    ),
                )
            if valid_feature:
                QTimer.singleShot(
                    1,
                    lambda: self.iface.mapCanvas().flashFeatureIds(
                        layer, [feature.id()]
                    ),
                )

    def _zoom_to_coordinate(self, x, y):
        if x and y:
            self._set_extend(x, y)
            self.iface.mapCanvas().flashGeometries(
                [QgsGeometry.fromPointXY(QgsPointXY(float(x), float(y)))]
            )

    def _set_extend(self, x, y):
        scale = 5
        rect = QgsRectangle(
            float(x) - scale, float(y) - scale, float(x) + scale, float(y) + scale
        )
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()

    def _pan_to_coordinate(self, x, y):
        self.iface.mapCanvas().setCenter(QgsPointXY(float(x), float(y)))
        self.iface.mapCanvas().refresh()

    def _open_form(self, t_ili_tid):
        layer, feature = self._get_feature_in_project(t_ili_tid)
        if layer and feature:
            self.iface.layerTreeView().setCurrentLayer(layer)
            self.iface.openFeatureForm(layer, feature, True)

    def _select_feature_in_attributetable(self, t_ili_tid):
        layer, feature = self._get_feature_in_project(t_ili_tid)
        if layer and feature:
            self.iface.layerTreeView().setCurrentLayer(layer)
            layer.removeSelection()
            layer.select(feature.id())
            attribute_table = self.iface.showAttributeTable(layer)
            if attribute_table:
                selected_filter_action = attribute_table.findChild(
                    QAction, "mActionSelectedFilter"
                )
                if selected_filter_action:
                    selected_filter_action.trigger()

    def _get_feature_in_project(self, t_ili_tid):
        for layer in QgsProject.instance().mapLayers().values():
            source_provider = layer.dataProvider()
            schema_identificator = (
                db_utils.get_schema_identificator_from_sourceprovider(source_provider)
            )
            if (
                schema_identificator
                and schema_identificator == self.current_schema_identificator
            ):
                if layer.type() == QgsMapLayer.VectorLayer:
                    idx = layer.fields().lookupField("t_ili_tid")
                    if idx < 0:
                        continue
                    for feature in layer.getFeatures():
                        if feature.attributes()[idx] == t_ili_tid:
                            return layer, feature
        return None, None

    def _auto_pan_button_clicked(self):
        if self.auto_pan_button.isChecked:
            self.auto_zoom_button.setChecked(False)

    def _auto_zoom_button_clicked(self):
        if self.auto_zoom_button.isChecked:
            self.auto_pan_button.setChecked(False)

    def _select_config_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select the validator config file")
        )
        if filename:
            self.config_file_line_edit.setText(self._relative_path(filename))

    def _save_config_file(self):
        filename = self.config_file_line_edit.text()

        QgsExpressionContextUtils.setProjectVariable(
            QgsProject.instance(),
            "validator_config",
            self._relative_path(filename),
        )

    def _load_config_file(self):
        filename = QgsExpressionContextUtils.projectScope(
            QgsProject.instance()
        ).variable("validator_config")
        if filename:
            self.config_file_line_edit.setText(self._relative_path(filename))

    def _relative_path(self, path):
        if (
            os.path.isfile(path)
            and QgsProject.instance().homePath()
            and os.path.isabs(path)
        ):
            # if it's a saved project and the path is not (yet) relative
            return os.path.relpath(path, QgsProject.instance().homePath())
        else:
            return path

    def _absolute_path(self, path):
        if (
            os.path.isfile(path)
            and QgsProject.instance().homePath()
            and not os.path.isabs(path)
        ):
            # if it's a saved project and the path is not not absolute
            return os.path.join(path, QgsProject.instance().homePath(), path)
        else:
            return path

    def _validator_stdout(self, txt):
        lines = txt.strip().split("\n")
        for line in lines:
            logging.info(line)

    def _validator_stderr(self, txt):
        lines = txt.strip().split("\n")
        for line in lines:
            logging.error(line)
