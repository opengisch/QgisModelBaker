"""
/***************************************************************************
                              -------------------
        begin                : 17.11.2023
        git sha              : :%H$
        copyright            : (C) 2023 by Dave Signer
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

from qgis.core import QgsProject
from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt
from qgis.PyQt.QtWidgets import QHeaderView, QWidget

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.libs.modelbaker.utils.qgis_utils import QgisProjectUtils
from QgisModelBaker.utils.gui_utils import CheckDelegate

WIDGET_UI = gui_utils.get_ui_class("tid_config_panel.ui")


class TIDModel(QAbstractTableModel):
    """
    ItemModel providing all TIDs and default values of the passed project

    oid_settings is a dictionary like:
        {
            "Strasse":
            {
                "oid_domain": "STANDARDOID",
                "interlis_topic" : "OIDMadness_V1",
                "default_value_expression": "uuid()",
                "in_form": True
            }
            [...]
        }
    """

    class Columns(IntEnum):
        NAME = 0
        OID_DOMAIN = 1
        DEFAULT_VALUE = 2
        IN_FORM = 3

    def __init__(self):
        super().__init__()
        self.oid_settings = {}

    def columnCount(self, parent):
        return len(TIDModel.Columns)

    def rowCount(self, parent):
        return len(self.oid_settings.keys())

    def flags(self, index):
        if index.column() == TIDModel.Columns.IN_FORM:
            return Qt.ItemIsEnabled
        if index.column() == TIDModel.Columns.DEFAULT_VALUE:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

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
            if section == TIDModel.Columns.NAME:
                return self.tr("Layer")
            if section == TIDModel.Columns.OID_DOMAIN:
                return self.tr("TID (OID Type)")
            if section == TIDModel.Columns.DEFAULT_VALUE:
                return self.tr("Default Value Expression")
            if section == TIDModel.Columns.IN_FORM:
                return self.tr("Show")

    def data(self, index, role):
        if role == int(Qt.DisplayRole) or role == int(Qt.EditRole):
            key = list(self.oid_settings.keys())[index.row()]
            if index.column() == TIDModel.Columns.NAME:
                return f"{key} ({self.oid_settings[key]['interlis_topic']})"
            if index.column() == TIDModel.Columns.OID_DOMAIN:
                return self.oid_settings[key]["oid_domain"]
            if index.column() == TIDModel.Columns.DEFAULT_VALUE:
                return self.oid_settings[key]["default_value_expression"]
            if index.column() == TIDModel.Columns.IN_FORM:
                return self.oid_settings[key]["in_form"]
        return None

    def setData(self, index, data, role):
        if role == int(Qt.EditRole):
            if index.column() == TIDModel.Columns.DEFAULT_VALUE:
                key = list(self.oid_settings.keys())[index.row()]
                self.oid_settings[key]["default_value_expression"] = data
                self.dataChanged.emit(index, index)
            if index.column() == TIDModel.Columns.IN_FORM:
                key = list(self.oid_settings.keys())[index.row()]
                self.oid_settings[key]["in_form"] = data
                self.dataChanged.emit(index, index)
        return True

    def load_tid_config(self, qgis_project=None):
        self.beginResetModel()
        self.oid_settings = QgisProjectUtils(qgis_project).get_oid_settings()
        self.endResetModel()

    def save_tid_config(self, qgis_project=None):
        if qgis_project:
            QgisProjectUtils(qgis_project).set_oid_settings(self.oid_settings)


class TIDConfigPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.tid_model = TIDModel()
        self.tid_config_view.setModel(self.tid_model)

        self.tid_config_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.NAME, QHeaderView.Stretch
        )
        self.tid_config_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.OID_DOMAIN, QHeaderView.ResizeToContents
        )
        self.tid_config_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.DEFAULT_VALUE, QHeaderView.ResizeToContents
        )
        self.tid_config_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.IN_FORM, QHeaderView.ResizeToContents
        )

        self.tid_config_view.setItemDelegateForColumn(
            TIDModel.Columns.IN_FORM,
            CheckDelegate(self, Qt.EditRole),
        )

    def load_tid_config(self, qgis_project=QgsProject.instance()):
        self.tid_model.load_tid_config(qgis_project)

    def save_tid_config(self, qgis_project=QgsProject.instance()):
        self.tid_model.save_tid_config(qgis_project)
