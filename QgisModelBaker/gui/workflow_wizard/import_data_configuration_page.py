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


from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QComboBox, QHeaderView, QStyledItemDelegate, QWizardPage

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools
import QgisModelBaker.utils.db_utils as db_utils
from QgisModelBaker.gui.dataset_manager import DatasetManagerDialog

from ...utils import ui

PAGE_UI = ui.get_ui_class("workflow_wizard/import_data_configuration.ui")


class DatasetComboDelegate(QStyledItemDelegate):
    def __init__(self, parent, db_connector):
        super().__init__(parent)
        self.refresh_datasets(db_connector)

    def refresh_datasets(self, db_connector):
        if db_connector:
            datasets_info = db_connector.get_datasets_info()
            self.items = [record["datasetname"] for record in datasets_info]

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
        self.setTitle(title)

        self.workflow_wizard = parent

        self.workflow_wizard.import_data_file_model.sourceModel().setHorizontalHeaderLabels(
            [self.tr("Import File"), self.tr("Dataset")]
        )
        self.file_table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.file_table_view.setModel(self.workflow_wizard.import_data_file_model)
        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QHeaderView.InternalMove)

        self.db_connector = None

        self.datasetmanager_dlg = None
        self.datasetmanager_button.setCheckable(True)
        self.datasetmanager_button.clicked.connect(self._show_datasetmanager_dialog)

    def nextId(self):
        return self.workflow_wizard.next_id()

    def order_list(self):
        order_list = []
        for visual_index in range(0, self.file_table_view.verticalHeader().count()):
            order_list.append(
                self.file_table_view.verticalHeader().logicalIndex(visual_index)
            )
        return order_list

    def setup_dialog(self, basket_handling):
        if basket_handling:
            self.db_connector = db_utils.get_db_connector(
                self.workflow_wizard.import_data_configuration
            )
            # set defaults
            for row in range(self.workflow_wizard.import_data_file_model.rowCount()):
                index = self.workflow_wizard.import_data_file_model.index(row, 1)
                value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
                if not value:
                    self.workflow_wizard.import_data_file_model.setData(
                        index,
                        wizard_tools.DEFAULT_DATASETNAME,
                        int(wizard_tools.SourceModel.Roles.DATASET_NAME),
                    )

                self.file_table_view.setItemDelegateForColumn(
                    1, DatasetComboDelegate(self, self.db_connector)
                )
        else:
            self.file_table_view.setColumnHidden(1, True)
            self.datasetmanager_button.setHidden(True)

        # since it's not yet integrated but I keep it to remember
        self.model_label.setHidden(True)
        self.model_list_view.setHidden(True)
        self.ili2db_options_button.setHidden(True)
        self.chk_delete_data.setHidden(True)

    def _show_datasetmanager_dialog(self):
        if self.datasetmanager_dlg:
            self.datasetmanager_dlg.reject()
        else:
            self.datasetmanager_dlg = DatasetManagerDialog(
                self.workflow_wizard.iface, self, True
            )
            self.datasetmanager_dlg.setAttribute(Qt.WA_DeleteOnClose)
            self.datasetmanager_dlg.setWindowFlags(
                self.datasetmanager_dlg.windowFlags() | Qt.Tool
            )
            self.datasetmanager_dlg.show()
            self.datasetmanager_dlg.finished.connect(
                self._datasetmanager_dialog_finished
            )
            self.datasetmanager_button.setChecked(True)

    def _datasetmanager_dialog_finished(self):
        self.datasetmanager_button.setChecked(False)
        self.datasetmanager_dlg = None
        self.file_table_view.setItemDelegateForColumn(
            1, DatasetComboDelegate(self, self.db_connector)
        )
