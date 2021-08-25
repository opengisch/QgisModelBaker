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
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError

from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType
from QgisModelBaker.libili2db.ili2dbconfig import Ili2DbCommandConfiguration
from QgisModelBaker.gui.edit_dataset_name import EditDatasetDialog
from qgis.core import QgsProject

from qgis.PyQt.QtWidgets import (
    QDialog,
    QHeaderView,
    QTableView,
    QMessageBox
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

    def refresh_model(self, db_connector = None):
        self.beginResetModel()
        self.clear()
        if db_connector:
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                item = QStandardItem()
                item.setData(record['datasetname'], int(Qt.DisplayRole))
                item.setData(record['datasetname'], int(DatasetSourceModel.Roles.DATASETNAME))
                item.setData(record['t_id'], int(DatasetSourceModel.Roles.TID))
                self.appendRow(item)
        self.endResetModel()

class DatasetManagerDialog(QDialog, DIALOG_UI):

    def __init__(self, iface, parent=None, wizard_embedded = False):

        QDialog.__init__(self, parent)
        self.iface = iface
        self._close_editing()

        self.setupUi(self)
        self.buttonBox.accepted.connect(self._accepted)
        self.buttonBox.rejected.connect(self._rejected)

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

        self.type_combo_box.currentIndexChanged.connect(self._type_changed)

        if wizard_embedded:
            # when opened by the wizard it uses the current db connection settings and should not be changable
            self.db_frame.setHidden(True)

        self.dataset_model = DatasetSourceModel()
        self.dataset_tableview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dataset_tableview.horizontalHeader().hide()
        self.dataset_tableview.verticalHeader().hide()
        self.dataset_tableview.setSelectionMode(QTableView.SingleSelection)
        self.dataset_tableview.setModel(self.dataset_model)

        self._restore_configuration()

        #refresh the models on changing values but avoid massive db connects by timer
        self.refreshTimer = QTimer()
        self.refreshTimer.setSingleShot(True)
        self.refreshTimer.timeout.connect(lambda: self._refresh_datasets(self._updated_configuration()))

        for key, value in self._lst_panel.items():
            value.notify_fields_modified.connect(self._request_for_refresh_datasets)

        self._refresh_datasets(self._updated_configuration())

        self.add_button.clicked.connect(self._add_dataset)
        self.edit_button.clicked.connect(self._edit_dataset)
        self.create_baskets_button.clicked.connect(self._create_baskets)
        self.dataset_tableview.selectionModel().selectionChanged.connect( lambda: self._enable_dataset_handling(True))

    def _close_editing(self):
        editable_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            self.iface.vectorLayerTools().stopEditing(layer)
            if layer.isEditable():
                editable_layers.append(layer)
        if editable_layers:    
            warning_box = QMessageBox(self)
            warning_box.setIcon(QMessageBox.Warning)
            warning_title = self.tr("Layers still editable")
            warning_box.setWindowTitle(warning_title)
            warning_box.setText(self.tr("You have still layers in editable mode.\nIn case you modify datasets on the database of those layers, it could lead to database locks.\nEditable layers are:\n - {}").format('\n - '.join([layer.name() for layer in editable_layers])))
            warning_box.exec_()


    def _valid_selection(self):
        """
        Returns if at least one dataset is selected
        """
        return bool(self.dataset_tableview.selectedIndexes())

    def _enable_dataset_handling(self, enable):
        self.dataset_tableview.setEnabled(enable)
        self.add_button.setEnabled(enable)
        self.edit_button.setEnabled(self._valid_selection())
        self.create_baskets_button.setEnabled(self._valid_selection())

    def _type_changed(self):
        ili_mode = self.type_combo_box.currentData()
        db_id = ili_mode & ~DbIliMode.ili

        self.db_wrapper_group_box.setTitle(displayDbIliMode[db_id])

        # Refresh panels
        for key, value in self._lst_panel.items():
            is_current_panel_selected = db_id == key
            value.setVisible(is_current_panel_selected)
            if is_current_panel_selected:
                value._show_panel()
        self._refresh_datasets(self._updated_configuration())

    def _request_for_refresh_datasets(self):
        # hold refresh back
        self.refreshTimer.start(500)
        
    def _refresh_datasets(self, configuration):
        db_connector = self._get_db_connector(configuration)
        if db_connector and db_connector.get_basket_handling:
            self._enable_dataset_handling(True)
            return self.dataset_model.refresh_model(db_connector)
        else:
            self._enable_dataset_handling(False)
            return self.dataset_model.clear()

    def _add_dataset(self):
        db_connector = self._get_db_connector(self._updated_configuration())
        if db_connector and db_connector.get_basket_handling:
            edit_dataset_dialog = EditDatasetDialog(self, db_connector)
            edit_dataset_dialog.exec_()
        self._refresh_datasets(self._updated_configuration())

    def _edit_dataset(self):
        if self._valid_selection():
            db_connector = self._get_db_connector(self._updated_configuration())
            if db_connector and db_connector.get_basket_handling:
                dataset = (self.dataset_tableview.selectedIndexes()[0].data(int(DatasetSourceModel.Roles.TID)), self.dataset_tableview.selectedIndexes()[0].data(int(DatasetSourceModel.Roles.DATASETNAME)))
                edit_dataset_dialog = EditDatasetDialog(self, db_connector, dataset )
                edit_dataset_dialog.exec_()
            self._refresh_datasets(self._updated_configuration())

    def _create_baskets(self):
        if self._valid_selection():
            db_connector = self._get_db_connector(self._updated_configuration())
            if db_connector and db_connector.get_basket_handling:
                feedbacks = []
                for record in db_connector.get_topics_info():
                    dataset_tid = self.dataset_tableview.selectedIndexes()[0].data(int(DatasetSourceModel.Roles.TID))
                    status, message = db_connector.create_basket( dataset_tid, '.'.join([record['model'], record['topic']]))
                    feedbacks.append((status, message))
    
                info_box = QMessageBox(self)
                info_box.setIcon(QMessageBox.Warning if len([feedback for feedback in feedbacks if not feedback[0]]) else QMessageBox.Information)
                info_title = self.tr("Created baskets")
                info_box.setWindowTitle(info_title)
                info_box.setText('\n'.join([feedback[1] for feedback in feedbacks]))
                info_box.exec_()

    def _db_ili_version(self, configuration):
        """
        Returns the ili2db version the database has been created with or None if the database
        could not be detected as a ili2db database
        """ 
        db_connector = self._get_db_connector(configuration)
        if db_connector:
            return db_connector.ili_version()

    def _get_db_connector(self, configuration):
        schema = configuration.dbschema

        db_factory = self.db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        try:
            return db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            return None

    def _restore_configuration(self):
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
        self._type_changed()

    def _updated_configuration(self):
        configuration = Ili2DbCommandConfiguration()

        mode = self.type_combo_box.currentData()
        self._lst_panel[mode].get_fields(configuration)

        configuration.tool = mode
        configuration.db_ili_version = self._db_ili_version(configuration)
        configuration.dbschema = configuration.dbschema or configuration.database
        return configuration

    def _save_configuration(self, configuration):
        settings = QSettings()
        settings.setValue('QgisModelBaker/importtype',
                          self.type_combo_box.currentData().name)
        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        config_manager.save_config_in_qsettings()

    def _accepted(self):
        self._save_configuration(self._updated_configuration())
        self.close()

    def _rejected(self):
        self._restore_configuration()
        self.close()
