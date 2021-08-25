# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 06.07.2021
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
import os
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtWidgets import QGridLayout, QToolButton
from PyQt5.uic.uiparser import _parse_alignment

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QHeaderView,
    QStyledItemDelegate,
    QComboBox,
    QAction,
    QWidget,
    QHBoxLayout,
    QStyle,
    QStyleOptionComboBox,
    QApplication,
    QLayout,
    QFrame
)

from qgis.PyQt.QtGui import (
    QIcon,
    QStandardItemModel,
    QStandardItem
)

from qgis.PyQt.QtCore import (
    Qt,
    QVariant
)

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from QgisModelBaker.gui.panel.log_panel import LogPanel
from QgisModelBaker.gui.dataset_manager import DatasetManagerDialog
from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools

from ...utils import get_ui_class

PAGE_UI = get_ui_class('workflow_wizard/import_data_configuration.ui')
class DatasetComboDelegate(QStyledItemDelegate):
    def __init__(self, parent, db_connector):
        super().__init__(parent)
        self.refresh_datasets(db_connector)
    def refresh_datasets(self, db_connector):
        datasets_info = db_connector.get_datasets_info()
        self.items = [record['datasetname'] for record in datasets_info]
    def createEditor(self, parent, option, index):
        self.editor = QComboBox(parent)
        self.editor.addItems(self.items)
        return self.editor
    def setEditorData(self, editor, index):
        value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
        num = self.items.index(value) if value in self.items else 0
        editor.setCurrentIndex(num)
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, int(wizard_tools.SourceModel.Roles.DATASET_NAME))
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
class ImportDataConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setMinimumSize(600, 500)
        self.setTitle(title)

        self.workflow_wizard = parent

        self.workflow_wizard.import_data_file_model.sourceModel(
        ).setHorizontalHeaderLabels([self.tr('Import File'), self.tr('Dataset')])
        self.file_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.file_table_view.setModel(
            self.workflow_wizard.import_data_file_model)
        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QHeaderView.InternalMove)
            
        # self.ili2db_options = Ili2dbOptionsDialog()
        # self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        # self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

        self.db_connector = None

        self.datasetmanager_dlg = None
        self.datasetmanager_button.setCheckable(True)
        self.datasetmanager_button.clicked.connect(self._show_datasetmanager_dialog)

    def order_list(self):
        order_list = []
        for visual_index in range(0, self.file_table_view.verticalHeader().count()):
            order_list.append(
                self.file_table_view.verticalHeader().logicalIndex(visual_index))
        return order_list

    def setup_dialog(self):
        # setup dataset handling
        self.db_connector = self._get_db_connector(self.workflow_wizard.import_data_configuration)
        if self.db_connector.get_basket_handling():
            # set defaults
            for row in range( self.workflow_wizard.import_data_file_model.rowCount() ):
                index = self.workflow_wizard.import_data_file_model.index(row, 1)
                value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
                if not value:
                    self.workflow_wizard.import_data_file_model.setData(index, wizard_tools.DEFAULT_DATASETNAME, int(wizard_tools.SourceModel.Roles.DATASET_NAME))
                self.file_table_view.setItemDelegateForColumn(1, DatasetComboDelegate(self, self.db_connector))
        else:
            self.file_table_view.setColumnHidden(1, True)

        # since it's not yet integrated but I keep it to remember
        self.model_label.setHidden(True)
        self.model_list_view.setHidden(True)
        self.ili2db_options_button.setHidden(True)
        self.chk_delete_data.setHidden(True)

    def nextId(self):
        return self.workflow_wizard.next_id()

    def _get_db_connector(self, configuration):
        # migth be moved to db_utils...
        db_simple_factory = DbSimpleFactory()
        schema = configuration.dbschema

        db_factory = db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        try:
            return db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            return None

    def _show_datasetmanager_dialog(self):
        if self.datasetmanager_dlg:
            self.datasetmanager_dlg.reject()
        else:
            self.datasetmanager_dlg = DatasetManagerDialog(self.workflow_wizard.iface, self, True)
            self.datasetmanager_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.datasetmanager_dlg.setWindowFlags(self.datasetmanager_dlg.windowFlags() | Qt.Tool)
            self.datasetmanager_dlg.show()
            self.datasetmanager_dlg.finished.connect(self.datasetmanager_dialog_finished)
            self.datasetmanager_button.setChecked(True)
    
    def datasetmanager_dialog_finished(self):
        self.datasetmanager_button.setChecked(False)
        self.datasetmanager_dlg = None
        self.file_table_view.setItemDelegateForColumn(1, DatasetComboDelegate(self, self.db_connector))