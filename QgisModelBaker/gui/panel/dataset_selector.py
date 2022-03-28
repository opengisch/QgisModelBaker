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

from qgis.core import QgsDataSourceUri, QgsExpressionContextUtils, QgsProject
from qgis.PyQt.QtCore import QSortFilterProxyModel, Qt
from qgis.PyQt.QtWidgets import QComboBox, QWidget

from QgisModelBaker.libs.modelbaker.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils.db_utils import (
    get_configuration_from_layersource,
    get_schema_identificator_from_layersource,
)
from QgisModelBaker.libs.modelbaker.utils.qt_utils import slugify
from QgisModelBaker.utils.gui_utils import BasketSourceModel


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
            configuration = Ili2DbCommandConfiguration()
            valid, mode = get_configuration_from_layersource(
                source_name, source, configuration
            )
            if valid and mode:
                db_factory = self.db_simple_factory.create_factory(mode)
                config_manager = db_factory.get_db_command_config_manager(configuration)
                try:
                    db_connector = db_factory.get_db_connector(
                        config_manager.get_uri(), configuration.dbschema
                    )
                    if db_connector.get_basket_handling():
                        self.basket_model.reload_schema_baskets(
                            db_connector,
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
