# -*- coding: utf-8 -*-
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
from enum import IntEnum

from qgis.core import QgsDataSourceUri, QgsMapLayer, QgsProject
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QStandardItemModel
from qgis.PyQt.QtWidgets import QWizardPage

from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils import db_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/ili2dbsettings.ui")


class ParametersModel(QStandardItemModel):
    """
    ItemModel providing the ili2db setting properties
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
        if index.column() == ParametersModel.Columns.NAME:
            return Qt.ItemSelectable

        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == ParametersModel.Columns.NAME:
                return self.tr("Name")
            if section == ParametersModel.Columns.VALUE:
                return self.tr("Value")

    def data(self, index, role):
        if role == int(Qt.DisplayRole) or role == int(Qt.EditRole):
            if index.column() == ParametersModel.Columns.NAME:
                return "name"
                return list(self.parameters.keys())[index.row()]
            if index.column() == ParametersModel.Columns.VALUE:
                return "va"
                return list(self.parameters.values())[index.row()]

        return QStandardItemModel.data(self, index, role)

    def setData(self, index, role, data):
        if index.column() == ParametersModel.Columns.VALUE:
            key = list(self.parameters.keys())[index.row()]
            self.parameters[key] = data

        return QStandardItemModel.setData(self, index, role, data)

    def refresh_model(self, parameters):
        self.beginResetModel()
        self.parameters = parameters
        self.endResetModel()


class Ili2dbSettingsPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.setTitle(title)

        self.schema_combobox.currentIndexChanged.connect(self._schema_changed)

        self.parameters_model = ParametersModel(
            self.toppingmaker_wizard.topping_maker.metaconfig.ili2db_settings.parameters
        )
        self.parameters_table_view.setModel(self.parameters_model)

    def initializePage(self) -> None:
        # - [ ] Ist das der Ort Models etc zu laden? Diese Funktion wird aufgerufen, jedes mal wenn mit "next" auf die Seite kommt.
        self._refresh_combobox()
        return super().initializePage()

    def _refresh_combobox(self):
        self.schema_combobox.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                source_provider = layer.dataProvider()
                source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
                schema_identificator = (
                    db_utils.get_schema_identificator_from_layersource(
                        source_provider, source
                    )
                )
                if (
                    not schema_identificator
                    or self.schema_combobox.findText(schema_identificator) > -1
                ):
                    continue

                configuration = Ili2DbCommandConfiguration()
                valid, mode = db_utils.get_configuration_from_layersource(
                    source_provider, source, configuration
                )
                if valid and mode:
                    configuration.tool = mode
                    db_connector = db_utils.get_db_connector(configuration)
                    # only load it when it exists and metadata there (contains interlis data)
                    if (
                        db_connector.db_or_schema_exists()
                        or db_connector.metadata_exists()
                    ):
                        self.schema_combobox.addItem(schema_identificator, db_connector)

        self.schema_combobox.addItem(
            self.tr("Not loading ili2db settings from schema"), None
        )

    def _schema_changed(self):
        db_connector = self.schema_combobox.currentData()
        if db_connector:
            self.toppingmaker_wizard.topping_maker.metaconfig.ili2db_settings.parse_parameters_from_db(
                db_connector
            )
        else:
            self.toppingmaker_wizard.topping_maker.metaconfig.ili2db_settings.parameters = (
                {}
            )
        self.parameters_model.refresh_model(
            self.toppingmaker_wizard.topping_maker.metaconfig.ili2db_settings.parameters
        )
