# -*- coding: utf-8 -*-
"""
/***************************************************************************
    begin                :    01.08.2021
    git sha              :    :%H$
    copyright            :    (C) 2021 by Dave Signer
    email                :    avid at opengis ch
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
from enum import Enum

from qgis.core import QgsDataSourceUri, QgsExpressionContextUtils, QgsProject
from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QComboBox, QWidget

from QgisModelBaker.utils.db_utils import (
    get_configuration_from_layersource,
    get_schema_identificator_from_layersource,
)
from QgisModelBaker.utils.qt_utils import slugify

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory


class BasketSourceModel(QStandardItemModel):
    class Roles(Enum):
        DATASETNAME = Qt.UserRole + 1
        MODEL_TOPIC = Qt.UserRole + 2
        BASKET_TID = Qt.UserRole + 3
        # The SCHEMA_TOPIC_IDENTIFICATOR is a combination of db parameters and the topic
        # This because a dataset is usually valid per topic and db schema
        SCHEMA_TOPIC_IDENTIFICATOR = Qt.UserRole + 4

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()
        self.schema_baskets = {}

    def refresh(self):
        self.beginResetModel()
        self.clear()
        for schema_identificator in self.schema_baskets.keys():
            for basket in self.schema_baskets[schema_identificator]:
                item = QStandardItem()
                item.setData(basket["datasetname"], int(Qt.DisplayRole))
                item.setData(
                    basket["datasetname"], int(BasketSourceModel.Roles.DATASETNAME)
                )
                item.setData(basket["topic"], int(BasketSourceModel.Roles.MODEL_TOPIC))
                item.setData(
                    basket["basket_t_id"], int(BasketSourceModel.Roles.BASKET_TID)
                )
                item.setData(
                    f"{schema_identificator}_{slugify(basket['topic'])}",
                    int(BasketSourceModel.Roles.SCHEMA_TOPIC_IDENTIFICATOR),
                )
                self.appendRow(item)
        self.endResetModel()

    def reload_schema_baskets(self, db_connector, schema_identificator):
        baskets_info = db_connector.get_baskets_info()
        baskets = []
        for record in baskets_info:
            basket = {}
            basket["datasetname"] = record["datasetname"]
            basket["topic"] = record["topic"]
            basket["basket_t_id"] = record["basket_t_id"]
            baskets.append(basket)
        self.schema_baskets[schema_identificator] = baskets
        self.refresh()

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if role == Qt.DisplayRole:
            if item.data(int(BasketSourceModel.Roles.MODEL_TOPIC)).split(".")[1]:
                return f"{item.data(int(role))} ({item.data(int(BasketSourceModel.Roles.MODEL_TOPIC)).split('.')[1]})"
        return item.data(int(role))

    def clear_schema_baskets(self):
        self.schema_baskets = {}

    def schema_baskets_loaded(self, schema_identificator):
        return schema_identificator in self.schema_baskets


class DatasetSelector(QComboBox):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.setToolTip(self.tr("Dataset used as default value in form"))

        self.db_simple_factory = DbSimpleFactory()
        self.basket_model = BasketSourceModel()
        self.filtered_model = QSortFilterProxyModel()
        self.filtered_model.setSourceModel(self.basket_model)
        self.current_schema_topic_identificator = int(
            BasketSourceModel.Roles.SCHEMA_TOPIC_IDENTIFICATOR
        )
        self.filtered_model.setFilterRole(self.current_schema_topic_identificator)
        self.setModel(self.filtered_model)
        self.setEnabled(False)

    def set_current_layer(self, layer):
        if self.isEnabled():
            self.currentIndexChanged.disconnect(self._store_basket_tid)
            self.setEnabled(False)

        if not layer or not layer.dataProvider().isValid():
            return

        source_name = layer.dataProvider().name()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        schema_identificator = get_schema_identificator_from_layersource(
            source_name, source
        )
        layer_model_topic_name = (
            QgsExpressionContextUtils.layerScope(layer).variable("interlis_topic") or ""
        )

        # set the filter of the model according the current uri_identificator
        self.current_schema_topic_identificator = slugify(
            f"{schema_identificator}_{layer_model_topic_name}"
        )

        self.filtered_model.setFilterRegExp(
            f"{self.current_schema_topic_identificator}.*"
        )

        if not self.basket_model.schema_baskets_loaded(schema_identificator):
            valid, mode, configuration = get_configuration_from_layersource(
                source_name, source
            )
            if valid and mode:
                db_factory = self.db_simple_factory.create_factory(mode)
                config_manager = db_factory.get_db_command_config_manager(configuration)

                try:
                    self.basket_model.reload_schema_baskets(
                        db_factory.get_db_connector(
                            config_manager.get_uri(), configuration.dbschema
                        ),
                        schema_identificator,
                    )
                except:
                    # let it pass, it will have no entries what is okey
                    pass

        if self.filtered_model.rowCount():
            self._set_index(self.current_schema_topic_identificator)
            self._store_basket_tid(self.currentIndex())
            self.currentIndexChanged.connect(self._store_basket_tid)
            self.setEnabled(True)

    def reset_model(self, current_layer):
        self.basket_model.clear_schema_baskets()
        if current_layer:
            self.set_current_layer(current_layer)

    def _set_index(self, schema_topic_identificator):
        current_basket_tid = QgsExpressionContextUtils.projectScope(
            QgsProject.instance()
        ).variable(schema_topic_identificator)
        matches = self.filtered_model.match(
            self.filtered_model.index(0, 0),
            int(BasketSourceModel.Roles.BASKET_TID),
            current_basket_tid,
            1,
            Qt.MatchExactly,
        )
        if matches:
            self.setCurrentIndex(matches[0].row())

    def _store_basket_tid(self, index):
        model_index = self.model().index(index, 0)
        basket_tid = model_index.data(int(BasketSourceModel.Roles.BASKET_TID))
        QgsExpressionContextUtils.setProjectVariable(
            QgsProject.instance(), self.current_schema_topic_identificator, basket_tid
        )
