# -*- coding: utf-8 -*-
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
import os

from PyQt5.QtGui import QColor, QGuiApplication
from qgis.core import (
    QgsApplication,
    QgsDataSourceUri,
    QgsMapLayer,
    QgsProject,
    QgsRectangle,
)
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QStandardPaths, Qt, QTimer
from qgis.PyQt.QtWidgets import QAction, QDockWidget, QHeaderView, QMenu

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
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

VALID_COLOR = "#adde9b"

VALID_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #adde9b; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """

INVALID_COLOR = "#de9b9b"

INVALID_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #de9b9b; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """

NOSTATUS_STYLE = """
    QProgressBar {border: 2px solid grey;border-radius: 5px;}
    QProgressBar::chunk {background-color: #9bcade; width: 20px;}
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }
    """

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
                    QColor(VALID_COLOR)
                    if item.data(int(ValidationResultModel.Roles.FIXED))
                    else QColor(INVALID_COLOR)
                )
            if role == Qt.ToolTipRole:
                tooltip_text = "{type} at {tid}".format(
                    type=item.data(int(ValidationResultModel.Roles.TYPE)),
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
            self.result_model = None

    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)

        self.schema_validations = {}
        self.requested_roles = [ValidationResultModel.Roles.MESSAGE]

        self.current_configuration = ValidateConfiguration()
        self.current_schema_identificator = ""
        self.current_models_model = SchemaModelsModel()
        self.current_datasets_model = SchemaDatasetsModel()
        self.current_baskets_model = SchemaBasketsModel()
        self.current_filter_mode = SchemaDataFilterMode.NO_FILTER

        self.filter_data_panel = FilterDataPanel(self)
        self.filter_data_panel.setMaximumHeight(self.fontMetrics().lineSpacing() * 10)
        self.filter_layout.addWidget(self.filter_data_panel)
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

    def _reset_current_values(self):
        self.current_configuration = ValidateConfiguration()
        self.current_schema_identificator = ""
        self.current_models_model = SchemaModelsModel()
        self.current_datasets_model = SchemaDatasetsModel()
        self.current_baskets_model = SchemaBasketsModel()
        self.current_filter_mode = SchemaDataFilterMode.NO_FILTER

    def _reset_gui(self):
        self._reset_current_values()
        self.info_label.setText("")
        self.progress_bar.setTextVisible(False)
        self.setStyleSheet(NOSTATUS_STYLE)
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
        if not layer or layer and not layer.dataProvider().isValid():
            self.setDisabled(True)
            return

        source_provider = layer.dataProvider()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        schema_identificator = db_utils.get_schema_identificator_from_layersource(
            source_provider, source
        )
        if not schema_identificator:
            self.setDisabled(True)
            return
        if schema_identificator == self.current_schema_identificator:
            self.setEnabled(True)
            return

        self._reset_gui()

        self.current_schema_identificator = schema_identificator
        valid, mode = db_utils.get_configuration_from_layersource(
            source_provider, source, self.current_configuration
        )
        if valid and mode:
            output_file_name = "{}.xtf".format(self.current_schema_identificator)
            self.current_configuration.xtflog = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                output_file_name,
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
            self.filter_data_panel.setup_dialog(self._basket_handling())
            self.setDisabled(False)

    def _visibility_changed(self, visible):
        if visible:
            self.set_current_layer(self.iface.activeLayer())

    def _refresh_schemadata_models(self):
        db_connector = db_utils.get_db_connector(self.current_configuration)
        self.schema_validations[
            self.current_schema_identificator
        ].models_model.refresh_model(db_connector)
        self.schema_validations[
            self.current_schema_identificator
        ].datasets_model.refresh_model(db_connector)
        self.schema_validations[
            self.current_schema_identificator
        ].baskets_model.refresh_model(db_connector)
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
        self.setStyleSheet(NOSTATUS_STYLE)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self._disable_controls(True)
        validator = ilivalidator.Validator()
        if validator:
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

        self.progress_bar.setValue(20)
        validation_result_state = False
        with OverrideCursor(Qt.WaitCursor):
            try:
                validation_result_state = (
                    validator.run(edited_command) == ilivalidator.Validator.SUCCESS
                )
            except JavaNotFoundError:
                self.progress_bar.setValue(0)
                self.progress_bar.setFormat(self.tr("Ili2db validation problems"))
                self.progress_bar.setTextVisible(True)
                self._disable_controls(False)
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
            self.setStyleSheet(VALID_STYLE)
        else:
            self.progress_bar.setFormat(self.tr("Schema is not valid"))
            self.setStyleSheet(INVALID_STYLE)
        self.progress_bar.setTextVisible(True)
        self.result_table_view.setDisabled(valid)

    def _disable_controls(self, disable):
        self.run_button.setDisabled(disable)
        self.result_table_view.setDisabled(disable)

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
                self.tr("Open Feature Form"),
                self,
            )
            action_open_form.triggered.connect(lambda: self._open_form(t_ili_tid))
            menu.addAction(action_open_form)
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
        if not coord_x or not coord_y:
            return

        t_ili_tid = index.data(int(ValidationResultModel.Roles.TID))
        layer, feature = self._get_feature_in_project(t_ili_tid)
        if not layer or not feature:
            return

        if self.auto_pan_button.isChecked():
            QTimer.singleShot(
                1,
                lambda: self.iface.mapCanvas().panToFeatureIds(
                    layer, [feature.id()], False
                ),
            )
        elif self.auto_zoom_button.isChecked():
            QTimer.singleShot(
                1,
                lambda: self.iface.mapCanvas().zoomToFeatureIds(layer, [feature.id()]),
            )

        if self.flash_button.isChecked():
            QTimer.singleShot(
                1, lambda: self.iface.mapCanvas().flashFeatureIds(layer, [feature.id()])
            )

    def _zoom_to_coordinate(self, x, y):
        if x and y:
            scale = 50
            rect = QgsRectangle(
                float(x) - scale, float(y) - scale, float(x) + scale, float(y) + scale
            )
            self.iface.mapCanvas().setExtent(rect)
            self.iface.mapCanvas().refresh()

    def _open_form(self, t_ili_tid):
        layer, feature = self._get_feature_in_project(t_ili_tid)
        if layer and feature:
            self.iface.layerTreeView().setCurrentLayer(layer)
            self.iface.openFeatureForm(layer, feature, True)

    def _get_feature_in_project(self, t_ili_tid):
        for layer in QgsProject.instance().mapLayers().values():
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
