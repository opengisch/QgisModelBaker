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
from PyQt5.QtWidgets import QComboBox
from qgis.PyQt.QtWidgets import (
    QWidget,
    QAction,
    QGridLayout
)
from qgis.PyQt.QtCore import (
    Qt,
    QSortFilterProxyModel
)
from qgis.core import (
    QgsProject,
    QgsDataSourceUri,
    QgsExpressionContextUtils
)
from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem
)

from QgisModelBaker.utils.qt_utils import slugify
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration
from QgisModelBaker.libili2db.globals import DbIliMode
from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError, DBConnector
from QgisModelBaker.libili2db.ili2dbutils import JavaNotFoundError
from QgisModelBaker.utils.qt_utils import OverrideCursor

class DatasetSourceModel(QStandardItemModel):
    class Roles(Enum):
        DATASETNAME = Qt.UserRole + 1
        MODEL_TOPIC = Qt.UserRole + 2
        BASKET_TID = Qt.UserRole + 3
        # The DB_TOPIC_IDENTIFICATOR is a combination of db parameters and the topic
        # This because a dataset is usually valid per topic and db schema
        DB_TOPIC_IDENTIFICATOR = Qt.UserRole + 4

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def refresh_datasets(self, db_connector, db_identificator):
        self.beginResetModel()
        self.clear()
        item = QStandardItem()
        baskets_info = db_connector.get_baskets_info()
        for record in baskets_info:
            item = QStandardItem()
            item.setData(record['datasetname'], int(Qt.DisplayRole))
            item.setData(record['datasetname'], int(DatasetSourceModel.Roles.DATASETNAME))
            item.setData(record['topic'], int(DatasetSourceModel.Roles.MODEL_TOPIC))
            item.setData(record['basket_t_id'], int(DatasetSourceModel.Roles.BASKET_TID))
            item.setData(slugify(f"{db_identificator}_{record['topic']}"), int(DatasetSourceModel.Roles.DB_TOPIC_IDENTIFICATOR))
            self.appendRow(item)
        print(f'my row count is {self.rowCount()}')
        self.endResetModel()

class DatasetCombobox(QComboBox):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.db_simple_factory = DbSimpleFactory()

        self.source_model = DatasetSourceModel()
        self.filtered_model = QSortFilterProxyModel()
        self.filtered_model.setSourceModel(self.source_model)
        self.filtered_model.setFilterRole(int(DatasetSourceModel.Roles.DB_TOPIC_IDENTIFICATOR))
        self.setModel(self.filtered_model)

        self.currentIndexChanged.connect(self.set_basket_tid)

    def set_current_layer(self, layer):
        if not layer or not layer.dataProvider().isValid():
            self.setEnabled(False)
            return

        source_name = layer.dataProvider().name()
        source = QgsDataSourceUri(layer.dataProvider().dataSourceUri())
        db_identificator = self.make_db_identificator(source_name, source)
        layer_model_topic_name = QgsExpressionContextUtils.layerScope(layer).variable('interlis_topic')

        # set the filter of the model according the current uri_identificator
        db_topic_identificator = slugify(f"{db_identificator}_{layer_model_topic_name}")
        self.filtered_model.setFilterFixedString(db_topic_identificator)

        if self.filtered_model.rowCount() == 0:
            # when no datasets are found we check the database again
            mode = ''
            configuration = Ili2DbCommandConfiguration()
            if source_name == 'postgres':
                mode = DbIliMode.pg
                configuration.dbhost = source.host()
                configuration.dbusr = source.username()
                configuration.dbpwd = source.password()
                configuration.database = source.database()
                configuration.dbschema = source.schema()
            elif source_name == 'ogr':
                mode = DbIliMode.gpkg
                configuration.dbfile = source.uri().split('|')[0].strip()
            elif source_name == 'mssql':
                mode = DbIliMode.mssql
                configuration.dbhost = source.host()
                configuration.dbusr = source.username()
                configuration.dbpwd = source.password()
                configuration.database = source.database()
                configuration.dbschema = source.schema()
                        
            db_factory = self.db_simple_factory.create_factory( mode ) 
            config_manager = db_factory.get_db_command_config_manager(configuration)
            self.update_datasets(db_factory.get_db_connector( config_manager.get_uri(), configuration.dbschema), db_identificator)

        self.setEnabled(True)
        
    def update_datasets(self, db_connector, db_identificator = ''):
        self.source_model.refresh_datasets(db_connector, db_identificator)

    def make_db_identificator(self, source_name, source):
        if source_name == 'postgres' or source_name == 'mssql':
            return f'{source.host()}_{source.database()}_{source.schema()}'
        elif source_name == 'ogr':
            return source.uri().split('|')[0].strip()
        return ''

    def set_basket_tid(self, index ):
        model_index = self.model().index(index,0)
        basket_tid = model_index.data(int(DatasetSourceModel.Roles.BASKET_TID))
        db_topic_identificator = model_index.data(int(DatasetSourceModel.Roles.DB_TOPIC_IDENTIFICATOR))
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(),db_topic_identificator,basket_tid)
