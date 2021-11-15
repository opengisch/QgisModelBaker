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

from PyQt5.QtGui import QStandardItem, QStandardItemModel
from qgis.core import QgsDataSourceUri
from qgis.gui import QgsGui
from qgis.PyQt.QtCore import QStandardPaths, Qt
from qgis.PyQt.QtWidgets import QDockWidget, QHeaderView

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
        TID = Qt.UserRole + 3

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
                    print("sd")
                    id = error.attrib["TID"]
                    message = self.get_element_text(error.find(ns + "Message"))
                    tid = self.get_element_text(error.find(ns + "Tid"))
                    """
                    Type
                    ObjTag
                    Tid
                    TechId
                    UserId
                    IliQName
                    DataSource
                    Line
                    Geometry
                    TechDetails
                    """
                    item = QStandardItem()
                    item.setData(id, int(ValidationResultModel.Roles.ID))
                    item.setData(message, int(ValidationResultModel.Roles.MESSAGE))
                    item.setData(tid, int(ValidationResultModel.Roles.TID))
                    self.appendRow(item)
                    print(f"{message} {tid}")
        self.endResetModel()


class ValidationResultTableModel(ValidationResultModel):
    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(
            [self.tr("Id"), self.tr("Message"), self.tr("T_IliTid")]
        )

    def data(self, index, role):
        item = self.item(index.row(), 0)
        if item:
            if role == Qt.DisplayRole:
                if index.column() == 0:
                    return item.data(int(ValidationResultModel.Roles.ID))
                if index.column() == 1:
                    return item.data(int(ValidationResultModel.Roles.MESSAGE))
                if index.column() == 2:
                    return item.data(int(ValidationResultModel.Roles.TID))
            return item.data(role)


class ValidateDock(QDockWidget, DIALOG_UI):
    def __init__(self, base_config, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self.setupUi(self)
        self.db_simple_factory = DbSimpleFactory()
        QgsGui.instance().enableAutoGeometryRestore(self)
        self.info_label.setText("")
        self.setDisabled(True)
        self.run_button.clicked.connect(self.run)
        self.current_configuration = ValidateConfiguration()
        self.current_schema_identificator = ""
        self.result_models = {}
        self.result_table_view.setModel(ValidationResultTableModel())
        self.result_table_view.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )

    def set_current_layer(self, layer):
        self.info_label.setText("")
        self.setDisabled(True)

        if not layer or not layer.dataProvider().isValid():
            return

        source_name = layer.dataProvider().name()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        self.current_schema_identificator = get_schema_identificator_from_layersource(
            source_name, source
        )
        # layer_model_topic_name = (
        #    QgsExpressionContextUtils.layerScope(layer).variable("interlis_topic") or ""
        # )

        # set the filter of the model according the current uri_identificator
        # current_schema_topic_identificator = slugify(
        #    f"{schema_identificator}_{layer_model_topic_name}"
        # )

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
            self.info_label.setText(
                f"{self.current_schema_identificator}\n{layer.name()}\n{self.current_configuration.database} / {self.current_configuration.dbschema or self.current_configuration.dbfile}"
            )

            if self.result_models.get(self.current_schema_identificator):
                self.result_table_view.setModel(
                    self.result_models[self.current_schema_identificator]
                )
            self.setDisabled(False)

    def run(self, edited_command=None):
        validator = ilivalidator.Validator()
        if validator:
            validator.tool = self.current_configuration.tool
            validator.configuration = self.current_configuration

        validation_state = False
        with OverrideCursor(Qt.WaitCursor):
            self.setDisabled(True)
            try:
                validation_state = (
                    validator.run(edited_command) == ilivalidator.Validator.SUCCESS
                )
            except JavaNotFoundError:
                print("cannot make validation")
                self.setDisabled(False)
                return

        result_model = ValidationResultTableModel()
        result_model.configuration = self.current_configuration
        result_model.valid = validation_state
        result_model.reload()

        self.result_models[self.current_schema_identificator] = result_model
        self.result_table_view.setModel(
            self.result_models[self.current_schema_identificator]
        )

        self.setDisabled(False)
        print(
            f"Result here {self.result_models[self.current_schema_identificator].configuration.xtflog}"
        )
