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
        self.filtered_model.setFilterRole(
            int(BasketSourceModel.Roles.SCHEMA_TOPIC_IDENTIFICATOR)
        )
        self.setModel(self.filtered_model)
        self.setEnabled(False)

    def set_current_layer(self, layer):
        if self.isEnabled():
            self.currentIndexChanged.disconnect(self._store_basket_tid)
            self.setEnabled(False)

        if not layer or not layer.dataProvider() or not layer.dataProvider().isValid():
            return

        source_provider = layer.dataProvider()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        schema_identificator = get_schema_identificator_from_layersource(
            source_provider, source
        )
        if not schema_identificator:
            return
        layer_model_topic_name = (
            QgsExpressionContextUtils.layerScope(layer).variable("interlis_topic") or ""
        )

        # set the filter of the model according the current uri_identificator
        self.current_schema_topic_identificator = slugify(
            f"{schema_identificator}_{layer_model_topic_name}"
        )

        self.current_default_basket_topic = slugify(
            f"default_basket{'_' if layer_model_topic_name else ''}{layer_model_topic_name}"
        )

        if not self.basket_model.schema_baskets_loaded(schema_identificator):
            configuration = Ili2DbCommandConfiguration()
            valid, mode = get_configuration_from_layersource(
                source_provider, source, configuration
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
                    self.set_default_project_variables(schema_identificator)
                except:
                    # let it pass, it will have no entries what is okay
                    pass

        self.filtered_model.setFilterRegExp(
            f"{self.current_schema_topic_identificator}"
        )

        if self.filtered_model.rowCount():
            self._set_index(self.current_default_basket_topic)
            self._store_basket_tid(self.currentIndex())
            self.currentIndexChanged.connect(self._store_basket_tid)
            self.setEnabled(True)

    def reset_model(self, current_layer):
        self.basket_model.clear_schema_baskets()
        if current_layer:
            self.set_current_layer(current_layer)

    def _set_index(self, default_basket_topic):
        current_basket_tid = QgsExpressionContextUtils.projectScope(
            QgsProject.instance()
        ).variable(default_basket_topic)
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
            QgsProject.instance(), self.current_default_basket_topic, basket_tid
        )

    def set_default_project_variables(self, schema_identificator):
        print(self.basket_model.model_topics(schema_identificator))
        for model_topic in self.basket_model.model_topics(schema_identificator):
            self._store_default_basket_tid(schema_identificator, model_topic)

    def _store_default_basket_tid(self, schema_identificator, model_topic):
        default_basket_topic = slugify(
            f"default_basket{'_' if model_topic else ''}{model_topic}"
        )
        if not QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable(
            default_basket_topic
        ):
            schema_topic_identificator = slugify(
                f"{schema_identificator}_{model_topic}"
            )
            self.filtered_model.setFilterRegExp(f"{schema_topic_identificator}")
            first_index = self.model().index(0, 0)
            basket_tid = first_index.data(int(BasketSourceModel.Roles.BASKET_TID))
            QgsExpressionContextUtils.setProjectVariable(
                QgsProject.instance(), default_basket_topic, basket_tid
            )
