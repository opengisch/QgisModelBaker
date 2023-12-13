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


from enum import Enum, IntEnum

from qgis.core import QgsProject
from qgis.gui import QgsFieldExpressionWidget
from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyledItemDelegate,
    QWidget,
)

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.libs.modelbaker.utils.qgis_utils import QgisProjectUtils
from QgisModelBaker.utils.gui_utils import CheckDelegate

WIDGET_UI = gui_utils.get_ui_class("layer_tids_panel.ui")


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

    class Roles(Enum):
        LAYER = Qt.UserRole + 1

        def __int__(self):
            return self.value

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
                return self.tr("OID Type")
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
                return self.oid_settings[key]["oid_domain"] or "---"
            if index.column() == TIDModel.Columns.DEFAULT_VALUE:
                return self.oid_settings[key]["default_value_expression"]
            if index.column() == TIDModel.Columns.IN_FORM:
                return self.oid_settings[key]["in_form"]
        elif role == int(Qt.ToolTipRole):
            key = list(self.oid_settings.keys())[index.row()]
            if index.column() == TIDModel.Columns.NAME:
                return f"{key} ({self.oid_settings[key]['interlis_topic']})"
            if index.column() == TIDModel.Columns.OID_DOMAIN:
                message = self.tr(
                    "<html><head/><body><p>The OID format is not defined, you can use whatever you want, but it should always start with an underscore <code>_</code> or an alphanumeric value.</p></body></html>"
                )
                oid_domain = self.oid_settings[key].get("oid_domain", "")
                if oid_domain[-7:] == "UUIDOID":
                    message = self.tr(
                        "<html><head/><body><p>The OID should be an Universally Unique Identifier (OID TEXT*36).</p></body></html>"
                    )
                elif oid_domain[-11:] == "STANDARDOID":
                    message = self.tr(
                        """<html>
                        <body>
                        <p>
                        The OID format requireds an 8 char prefix and 8 char postfix.
                        </p>
                        <p><b>Prefix (2 + 6 chars):</b> Country identifier + a 'global' identification part assigned once by the official authority.</p>
                        </p><p><b>Postfix (8 chars):</b> Sequence (numeric or alphanumeric) of your system as 'local' identification part.</p>
                        </body>
                        </html>
                """
                    )
                elif oid_domain[-6:] == "I32OID":
                    message = self.tr(
                        "<html><head/><body><p>The OID must be an integer value (OID 0 .. 2147483647).</p></body></html>"
                    )
                elif oid_domain[-6:] == "ANYOID":
                    message = self.tr(
                        "<html><head/><body><p>The OID format could vary depending in what basket the object (entry) is located.</p><p>These objects could be in the following topics: {topics}</body></html>".format(
                            topics=self.oid_settings[key]["interlis_topic"]
                        )
                    )
                return message
            if index.column() == TIDModel.Columns.DEFAULT_VALUE:
                return self.oid_settings[key]["default_value_expression"]
            if index.column() == TIDModel.Columns.IN_FORM:
                return self.tr("Show t_ili_tid field (OID) in attribute form.")
        elif role == int(TIDModel.Roles.LAYER):
            key = list(self.oid_settings.keys())[index.row()]
            return self.oid_settings[key]["layer"]
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


class FieldExpressionDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editor = None

    def createEditor(self, parent, option, index):
        self.editor = QgsFieldExpressionWidget(parent)
        layer = index.data(int(TIDModel.Roles.LAYER))
        self.editor.setLayer(layer)
        return self.editor

    def setEditorData(self, editor, index):
        value = index.data(int(Qt.DisplayRole))
        self.editor.setExpression(value)

    def setModelData(self, editor, model, index):
        value = editor.expression()
        print(f"new exp{value}")
        model.setData(index, value, int(Qt.EditRole))

    def updateEditorGeometry(self, editor, option, index):
        self.editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        opt = self.createEditor(self.parent, option, index)
        opt.editable = False
        value = index.data(int(Qt.DisplayRole))
        opt.setExpression(value)
        opt.resize(option.rect.width(), option.rect.height())
        pixmap = QPixmap(opt.width(), opt.height())
        opt.render(pixmap)
        painter.drawPixmap(option.rect, pixmap)
        painter.restore()


class LayerTIDsPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.tid_model = TIDModel()
        self.layer_tids_view.setModel(self.tid_model)

        self.layer_tids_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.NAME, QHeaderView.Stretch
        )
        self.layer_tids_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.OID_DOMAIN, QHeaderView.ResizeToContents
        )
        self.layer_tids_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.DEFAULT_VALUE, QHeaderView.ResizeToContents
        )
        self.layer_tids_view.horizontalHeader().setSectionResizeMode(
            TIDModel.Columns.IN_FORM, QHeaderView.ResizeToContents
        )

        self.layer_tids_view.setItemDelegateForColumn(
            TIDModel.Columns.IN_FORM,
            CheckDelegate(self, Qt.EditRole),
        )
        self.layer_tids_view.setItemDelegateForColumn(
            TIDModel.Columns.DEFAULT_VALUE,
            FieldExpressionDelegate(self),
        )
        self.layer_tids_view.setEditTriggers(QAbstractItemView.AllEditTriggers)

    def load_tid_config(self, qgis_project=QgsProject.instance()):
        self.tid_model.load_tid_config(qgis_project)

    def save_tid_config(self, qgis_project=QgsProject.instance()):
        # if a cell is still edited, we need to store it in model by force
        index = self.layer_tids_view.currentIndex()
        self.layer_tids_view.currentChanged(index, index)
        self.tid_model.save_tid_config(qgis_project)
