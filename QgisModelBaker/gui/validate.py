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
import xml.etree.cElementTree as CET
from enum import Enum

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsDataSourceUri, QgsProject, QgsRectangle
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QStandardPaths, Qt
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
)

from QgisModelBaker.libili2db.globals import DbIliMode
from QgisModelBaker.libili2db.ili2dbconfig import ValidateConfiguration
from QgisModelBaker.libili2db.ili2dbutils import JavaNotFoundError
from QgisModelBaker.utils.db_utils import (
    get_configuration_from_layersource,
    get_schema_identificator_from_layersource,
)
from QgisModelBaker.utils.qt_utils import OverrideCursor

from ..libili2db import ilivalidator
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..utils import ui

DIALOG_UI = ui.get_ui_class("validator.ui")

# validate tools
class ValidationResultModel(QStandardItemModel):
    class Roles(Enum):
        ID = Qt.UserRole + 1
        MESSAGE = Qt.UserRole + 2
        TYPE = Qt.UserRole + 3
        OBJ_TAG = Qt.UserRole + 4
        TID = Qt.UserRole + 5
        TECH_ID = Qt.UserRole + 6
        USER_ID = Qt.UserRole + 7
        ILI_Q_NAME = Qt.UserRole + 8
        DATA_SOURCE = Qt.UserRole + 9
        LINE = Qt.UserRole + 10
        COORD_X = Qt.UserRole + 11
        COORD_Y = Qt.UserRole + 12
        TECH_DETAILS = Qt.UserRole + 13

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self.configuration = ValidateConfiguration()
        self.valid = False

    def get_element_text(self, element):
        if element is not None:
            return element.text
        return None

    def reload(self):
        self.beginResetModel()
        if self.configuration.xtflog:
            try:
                root = CET.parse(self.configuration.xtflog).getroot()
            except CET.ParseError as e:
                print(
                    self.tr(
                        "Could not parse ilidata file `{file}` ({exception})".format(
                            file=self.configuration.xtflog, exception=str(e)
                        )
                    )
                )
            if root:
                ns = "{http://www.interlis.ch/INTERLIS2.3}"
                for error in root.iter(ns + "IliVErrors.ErrorLog.Error"):
                    id = error.attrib["TID"]
                    message = self.get_element_text(error.find(ns + "Message"))
                    type = self.get_element_text(error.find(ns + "Type"))
                    obj_tag = self.get_element_text(error.find(ns + "ObjTag"))
                    tid = self.get_element_text(error.find(ns + "Tid"))
                    tech_id = self.get_element_text(error.find(ns + "TechId"))
                    user_id = self.get_element_text(error.find(ns + "UserId"))
                    ili_q_name = self.get_element_text(error.find(ns + "IliQName"))
                    data_source = self.get_element_text(error.find(ns + "DataSource"))
                    line = self.get_element_text(error.find(ns + "Line"))
                    coord_x = None
                    coord_y = None
                    geometry = error.find(ns + "Geometry")
                    if geometry:
                        coord = geometry.find(ns + "COORD")
                        if coord:
                            coord_x = self.get_element_text(coord.find(ns + "C1"))
                            coord_y = self.get_element_text(coord.find(ns + "C2"))
                    tech_details = self.get_element_text(error.find(ns + "TechDetails"))

                    if type in ["Error", "Warning"]:
                        item = QStandardItem()
                        item.setData(id, int(ValidationResultModel.Roles.ID))
                        item.setData(message, int(ValidationResultModel.Roles.MESSAGE))
                        item.setData(type, int(ValidationResultModel.Roles.TYPE))
                        item.setData(obj_tag, int(ValidationResultModel.Roles.OBJ_TAG))
                        item.setData(tid, int(ValidationResultModel.Roles.TID))
                        item.setData(tech_id, int(ValidationResultModel.Roles.TECH_ID))
                        item.setData(user_id, int(ValidationResultModel.Roles.USER_ID))
                        item.setData(
                            ili_q_name, int(ValidationResultModel.Roles.ILI_Q_NAME)
                        )
                        item.setData(
                            data_source, int(ValidationResultModel.Roles.DATA_SOURCE)
                        )
                        item.setData(line, int(ValidationResultModel.Roles.LINE))
                        item.setData(coord_x, int(ValidationResultModel.Roles.COORD_X))
                        item.setData(coord_y, int(ValidationResultModel.Roles.COORD_Y))
                        item.setData(
                            tech_details, int(ValidationResultModel.Roles.TECH_DETAILS)
                        )
                        self.appendRow(item)
        self.endResetModel()


class ValidationResultTableModel(ValidationResultModel):
    """
    roles can define on what position what role should be provided
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
            return item.data(role)


class OpenFormDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            value = f"t_ili_tid {index.data(int(ValidationResultModel.Roles.TID))}"
            print(value)
            return True
        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        opt = QStyleOptionButton()
        opt.rect = option.rect
        QApplication.style().drawControl(QStyle.CE_PushButton, opt, painter)


class ValidateDock(QDockWidget, DIALOG_UI):
    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.run_button.clicked.connect(self.run)
        self.result_models = {}
        self.requested_roles = [
            ValidationResultModel.Roles.TID,
            ValidationResultModel.Roles.MESSAGE,
            ValidationResultModel.Roles.TYPE,
        ]
        self._reset_gui()
        self.result_table_view.clicked.connect(self._table_clicked)
        self.visibilityChanged.connect(self._visibility_changed)

    def _table_clicked(self):
        index = self.result_table_view.selectionModel().currentIndex()
        coord_x = index.sibling(index.row(), index.column()).data(
            int(ValidationResultModel.Roles.COORD_X)
        )
        coord_y = index.sibling(index.row(), index.column()).data(
            int(ValidationResultModel.Roles.COORD_Y)
        )
        self._zoom_to_coordinate(coord_x, coord_y)

        t_ili_tid = index.sibling(index.row(), index.column()).data(
            int(ValidationResultModel.Roles.TID)
        )
        if t_ili_tid:
            layer, feature = self._get_feature_in_project(t_ili_tid)
            if layer and feature:
                self.iface.openFeatureForm(layer, feature, True)

    def _visibility_changed(self, visible):
        if visible:
            self.set_current_layer(self.iface.activeLayer())

    def _reset_gui(self):
        self.current_configuration = ValidateConfiguration()
        self.current_schema_identificator = ""
        self.info_label.setText("")
        self.progress_bar.setTextVisible(False)
        self.result_table_view.setModel(
            ValidationResultTableModel(self.requested_roles)
        )
        self.result_table_view.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.result_table_view.setWordWrap(True)
        self.result_table_view.setTextElideMode(Qt.ElideLeft)
        self.result_table_view.resizeRowsToContents()
        self.result_table_view.verticalHeader().hide()
        self.result_table_view.setSelectionBehavior(QHeaderView.SelectRows)
        self.setDisabled(True)

    def set_current_layer(self, layer):
        if not layer or not layer.dataProvider().isValid():
            self._reset_gui()
            return

        source_name = layer.dataProvider().name()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        schema_identificator = get_schema_identificator_from_layersource(
            source_name, source
        )
        if schema_identificator == self.current_schema_identificator:
            return

        self._reset_gui()

        self.current_schema_identificator = schema_identificator
        valid, mode = get_configuration_from_layersource(
            source_name, source, self.current_configuration
        )
        if valid and mode:
            output_file_name = "{}.xtf".format(self.current_schema_identificator)
            self.current_configuration.xtflog = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.TempLocation),
                output_file_name,
            )
            self.current_configuration.tool = mode
            if mode == DbIliMode.gpkg:
                self.info_label.setText(self.current_configuration.dbfile)
            else:
                self.info_label.setText(
                    f'Database "{self.current_configuration.database}" and schema "{self.current_configuration.dbschema}"'
                )

            if self.result_models.get(self.current_schema_identificator):
                self._set_result(
                    self.result_models[self.current_schema_identificator].valid
                )
            self.setDisabled(False)

    def run(self, edited_command=None):
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self._disable_controls(True)
        validator = ilivalidator.Validator()
        if validator:
            validator.tool = self.current_configuration.tool
            validator.configuration = self.current_configuration

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
        self.result_models[self.current_schema_identificator] = result_model
        self._disable_controls(False)
        self._set_result(self.result_models[self.current_schema_identificator].valid)
        self.progress_bar.setValue(100)

        print(
            f"Result here {self.result_models[self.current_schema_identificator].configuration.xtflog}"
        )

    def _set_result(self, valid):
        self.result_table_view.setModel(
            self.result_models[self.current_schema_identificator]
        )
        """
        not sure if we should make it like this
        self.result_table_view.setItemDelegateForColumn(
            0,
            OpenFormDelegate(self),
        )
        """
        self.progress_bar.setFormat(
            self.tr("Schema is valid") if valid else self.tr("Schema is not valid")
        )
        self.progress_bar.setTextVisible(True)
        self.result_table_view.setDisabled(valid)

    def _disable_controls(self, disable):
        self.run_button.setDisabled(disable)
        self.result_table_view.setDisabled(disable)

    def _zoom_to_coordinate(self, x, y):
        if x and y:
            scale = 50
            rect = QgsRectangle(
                float(x) - scale, float(y) - scale, float(x) + scale, float(y) + scale
            )
            self.iface.mapCanvas().setExtent(rect)
            self.iface.mapCanvas().refresh()

    def _get_feature_in_project(self, t_ili_tid):
        for layer in QgsProject.instance().mapLayers().values():
            idx = layer.fields().lookupField("t_ili_tid")
            if idx < 0:
                continue
            for feature in layer.getFeatures():
                if feature.attributes()[idx] == t_ili_tid:
                    return layer, feature
        return None, None
