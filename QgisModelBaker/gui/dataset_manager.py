# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 10.08.2021
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
from enum import Enum
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration

from qgis.PyQt.QtWidgets import (
    QDialog,
    QHeaderView,
    QTableView,
    QSizePolicy
)
from qgis.PyQt.QtCore import (
    QSettings,
    QTimer,
    Qt
)
from ..utils import get_ui_class

from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem
)

DIALOG_UI = get_ui_class('dataset_manager.ui')

class DatasetSourceModel(QStandardItemModel):
    class Roles(Enum):
        TID = Qt.UserRole + 1
        DATASETNAME = Qt.UserRole + 2

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def reload_datasets(self, db_connector):
        datasets_info = db_connector.get_datasets_info()

        print( datasets_info)
        self.beginResetModel()
        self.clear()
        for record in datasets_info:
            item = QStandardItem()
            print(record)
            item.setData(record['datasetname'], int(Qt.DisplayRole))
            item.setData(record['datasetname'], int(DatasetSourceModel.Roles.DATASETNAME))
            item.setData(record['t_id'], int(DatasetSourceModel.Roles.TID))
            self.appendRow(item)
        self.endResetModel()

class DatasetManagerDialog(QDialog, DIALOG_UI):

    def __init__(self, parent=None):

        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accepted)
        self.buttonBox.rejected.connect(self.rejected)

        self.type_combo_box.clear()
        self._lst_panel = dict()
        self.db_simple_factory = DbSimpleFactory()

        for db_id in self.db_simple_factory.get_db_list(False):
            self.type_combo_box.addItem(displayDbIliMode[db_id], db_id)
            db_factory = self.db_simple_factory.create_factory(db_id)
            item_panel = db_factory.get_config_panel(
                self, DbActionType.EXPORT)
            self._lst_panel[db_id] = item_panel
            self.db_layout.addWidget(item_panel)

        self.type_combo_box.currentIndexChanged.connect(self.type_changed)

        self.dataset_model = DatasetSourceModel()
        self.dataset_model.setHorizontalHeaderLabels([self.tr('Name'),'213'])
        self.dataset_tableview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dataset_tableview.setModel(self.dataset_model)

        self.restore_configuration()

        #refresh the models on changing values but avoid massive db connects by timer
        self.refreshTimer = QTimer()
        self.refreshTimer.setSingleShot(True)
        self.refreshTimer.timeout.connect(self.refresh_datasets)

        for key, value in self._lst_panel.items():
            value.notify_fields_modified.connect(self.request_for_refresh_datasets)

        self.reload_datasets(self.updated_configuration())

    def request_for_refresh_datasets(self):
        # hold refresh back
        self.refreshTimer.start(500)

    def refresh_datasets(self):
        self.reload_datasets(self.updated_configuration())
        
    def type_changed(self):
        ili_mode = self.type_combo_box.currentData()
        db_id = ili_mode & ~DbIliMode.ili

        self.db_wrapper_group_box.setTitle(displayDbIliMode[db_id])

        # Refresh panels
        for key, value in self._lst_panel.items():
            is_current_panel_selected = db_id == key
            value.setVisible(is_current_panel_selected)
            if is_current_panel_selected:
                value._show_panel()
        self.reload_datasets(self.updated_configuration())

    def reload_datasets(self, configuration):
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        db_connector = None

        try:
            db_connector = db_factory.get_db_connector(uri_string, schema)
            if db_connector.get_basket_handling:
                return self.dataset_model.reload_datasets(db_connector)
            else:
                return self.dataset_model.clear()
        except (DBConnectorError, FileNotFoundError):
            return None


    def accepted(self):
        self.save_configuration(self.updated_configuration())
        self.close()

    def rejected(self):
        self.restore_configuration()
        self.close()

    def db_ili_version(self, configuration):
        """
        Returns the ili2db version the database has been created with or None if the database
        could not be detected as a ili2db database
        """
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        db_connector = None

        try:
            db_connector = db_factory.get_db_connector(uri_string, schema)
            return db_connector.ili_version()
        except (DBConnectorError, FileNotFoundError):
            return None

    def restore_configuration(self):
        settings = QSettings()

        for db_id in self.db_simple_factory.get_db_list(False):
            configuration = Ili2DbCommandConfiguration()
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager( configuration)
            config_manager.load_config_from_qsettings()
            self._lst_panel[db_id].set_fields(configuration)

        mode = settings.value('QgisModelBaker/importtype')
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database
        mode = mode & ~DbIliMode.ili

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self.type_changed()

    def updated_configuration(self):
        configuration = Ili2DbCommandConfiguration()

        mode = self.type_combo_box.currentData()
        self._lst_panel[mode].get_fields(configuration)

        configuration.tool = mode
        configuration.db_ili_version = self.db_ili_version(configuration)
        configuration.dbschema = configuration.dbschema or configuration.database
        return configuration

    def save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgisModelBaker/importtype',
                          self.type_combo_box.currentData().name)
        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()
