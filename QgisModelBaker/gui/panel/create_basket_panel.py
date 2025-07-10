"""
/***************************************************************************
                              -------------------
        begin                : 20.11.2023
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


import uuid
from enum import IntEnum

from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt
from qgis.PyQt.QtWidgets import QAbstractItemView, QHeaderView, QWidget

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils.gui_utils import CheckDelegate

WIDGET_UI = gui_utils.get_ui_class("basket_panel.ui")


class CreateBasketModel(QAbstractTableModel):
    """
    ItemModel providing possible (non-existing) baskets in the given dataset,
    based on keys model-topic.
    It provides the topic and the suggested BIDs (t_ili_tid), as well as
    the option if it should be created.
    """

    class Columns(IntEnum):
        DO_CREATE = 0
        TOPIC = 1
        BID_DOMAIN = 2
        BID_VALUE = 3
        ATTACHMENT_KEY = 4

    def __init__(self):
        super().__init__()
        self.basket_settings = {}

    def columnCount(self, parent):
        return len(CreateBasketModel.Columns)

    def rowCount(self, parent):
        return len(self.basket_settings)

    def flags(self, index):
        if index.column() == CreateBasketModel.Columns.DO_CREATE:
            return Qt.ItemFlag.ItemIsEnabled
        if index.column() in (
            CreateBasketModel.Columns.BID_VALUE,
            CreateBasketModel.Columns.ATTACHMENT_KEY,
        ):
            return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

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
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section == CreateBasketModel.Columns.DO_CREATE:
                return self.tr("Create")
            if section == CreateBasketModel.Columns.TOPIC:
                return self.tr("Topic")
            if section == CreateBasketModel.Columns.BID_DOMAIN:
                return self.tr("BID (OID Type)")
            if section == CreateBasketModel.Columns.BID_VALUE:
                return self.tr("BID Value")
            if section == CreateBasketModel.Columns.ATTACHMENT_KEY:
                return self.tr("Attachment key")

    def data(self, index, role):
        if role == int(Qt.ItemDataRole.DisplayRole) or role == int(
            Qt.ItemDataRole.EditRole
        ):
            key = list(self.basket_settings.keys())[index.row()]
            if index.column() == CreateBasketModel.Columns.DO_CREATE:
                return self.basket_settings[key]["create"]
            if index.column() == CreateBasketModel.Columns.TOPIC:
                return key
            if index.column() == CreateBasketModel.Columns.BID_DOMAIN:
                return self.basket_settings[key]["bid_domain"] or "---"
            if index.column() == CreateBasketModel.Columns.BID_VALUE:
                return self.basket_settings[key]["bid_value"]
            if index.column() == CreateBasketModel.Columns.ATTACHMENT_KEY:
                return self.basket_settings[key]["attachmentkey"]
        elif role == int(Qt.ItemDataRole.ToolTipRole):
            key = list(self.basket_settings.keys())[index.row()]
            if index.column() == CreateBasketModel.Columns.DO_CREATE:
                return self.tr("If this basket should be created")
            if index.column() == CreateBasketModel.Columns.TOPIC:
                return key
            if index.column() == CreateBasketModel.Columns.BID_DOMAIN:
                message = self.tr(
                    "<html><head/><body><p>The OID format is not defined, you can use whatever you want, but it should always start with an underscore <code>_</code> or an alphanumeric value.</p></body></html>"
                )
                oid_domain = self.basket_settings[key].get("oid_domain", "")
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
                            topics=self.basket_settings[key]["interlis_topic"]
                        )
                    )
                return message
            if index.column() == CreateBasketModel.Columns.BID_VALUE:
                return "<html><head/><body><p>Use `{t_id}` as placeholder when you want to use the next T_Id sequence value.</body></html>"
        return None

    def setData(self, index, data, role):
        if role == int(Qt.ItemDataRole.EditRole):
            key = list(self.basket_settings.keys())[index.row()]
            if index.column() == CreateBasketModel.Columns.BID_VALUE:
                self.basket_settings[key]["bid_value"] = data
                self.dataChanged.emit(index, index)
            if index.column() == CreateBasketModel.Columns.ATTACHMENT_KEY:
                self.basket_settings[key]["attachmentkey"] = data
                self.dataChanged.emit(index, index)
            if index.column() == CreateBasketModel.Columns.DO_CREATE:
                self.basket_settings[key]["create"] = data
                self.dataChanged.emit(index, index)
        return True

    def load_basket_config(self, db_connector, dataset):
        self.beginResetModel()
        self.basket_settings.clear()
        for topic_record in db_connector.get_topics_info():
            basket_setting = {}

            topic_key = f"{topic_record['model']}.{topic_record['topic']}"
            # check if existing
            existing = False
            for basket_record in db_connector.get_baskets_info():
                if (
                    basket_record["datasetname"] == dataset
                    and topic_key == basket_record["topic"]
                ):
                    existing = True
                    break

            if not existing:
                # if not existing "suggest" create if "relevant"
                basket_setting["create"] = topic_record["relevance"]
                basket_setting["bid_domain"] = topic_record["bid_domain"]

                # set suggestion of value
                if basket_setting["bid_domain"] == "INTERLIS.UUIDOID":
                    basket_setting["bid_value"] = str(uuid.uuid4())
                elif basket_setting["bid_domain"] == "INTERLIS.STANDARDOID":
                    basket_setting["bid_value"] = "%change%{t_id}"
                elif basket_setting["bid_domain"] == "INTERLIS.I32OID":
                    basket_setting["bid_value"] = "{t_id}"
                else:
                    basket_setting["bid_value"] = f"_{uuid.uuid4()}"

                basket_setting["attachmentkey"] = "modelbaker"  # Default

                self.basket_settings[topic_key] = basket_setting
        self.endResetModel()

    def _next_tid_value(self, db_connector):
        return db_connector.get_next_ili2db_sequence_value()

    def save_basket_config(self, db_connector, dataset):
        feedbacks = []
        datasets_info = db_connector.get_datasets_info()
        dataset_tid = -1
        for dataset_record in datasets_info:
            if dataset_record["datasetname"] == dataset:
                dataset_tid = dataset_record["t_id"]
                break
        if dataset_tid < 0:
            feedbacks.append((False, self.tr("Dataset needs to be created first.")))
        else:
            for topic_key in self.basket_settings.keys():
                basket_setting = self.basket_settings[topic_key]
                if basket_setting["create"]:
                    # basket should be created
                    status, message = db_connector.create_basket(
                        dataset_tid,
                        topic_key,
                        basket_setting["bid_value"].format(
                            t_id=f"{self._next_tid_value(db_connector):08}"
                            if len(basket_setting["bid_value"]) > 6
                            else self._next_tid_value(db_connector)
                        ),
                        basket_setting["attachmentkey"],
                    )
                    feedbacks.append((status, message))
        return feedbacks


class CreateBasketPanel(QWidget, WIDGET_UI):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.bid_model = CreateBasketModel()
        self.basket_view.setModel(self.bid_model)

        self.basket_view.horizontalHeader().setSectionResizeMode(
            CreateBasketModel.Columns.DO_CREATE, QHeaderView.ResizeMode.ResizeToContents
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            CreateBasketModel.Columns.TOPIC, QHeaderView.ResizeMode.Stretch
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            CreateBasketModel.Columns.BID_DOMAIN,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            CreateBasketModel.Columns.BID_VALUE, QHeaderView.ResizeMode.ResizeToContents
        )
        self.basket_view.horizontalHeader().setSectionResizeMode(
            CreateBasketModel.Columns.ATTACHMENT_KEY,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.basket_view.setItemDelegateForColumn(
            CreateBasketModel.Columns.DO_CREATE,
            CheckDelegate(self, Qt.ItemDataRole.EditRole),
        )
        self.basket_view.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)

    def load_basket_config(self, db_connector, dataset):
        self.bid_model.load_basket_config(db_connector, dataset)

    def save_basket_config(self, db_connector, dataset):
        # if a cell is still edited, we need to store it in model by force
        index = self.basket_view.currentIndex()
        self.basket_view.currentChanged(index, index)

        return self.bid_model.save_basket_config(db_connector, dataset)
