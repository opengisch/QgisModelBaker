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

import os

from PyQt5.QtWidgets import QApplication
from qgis.PyQt.QtCore import QEvent, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionComboBox,
    QWizardPage,
)

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
            self.items = [
                record["datasetname"]
                for record in datasets_info
                if record["datasetname"] != wizard_tools.CATALOGUE_DATASETNAME
            ]

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

    def editorEvent(self, event, model, option, index):
        # trying to make the combo open on single click because it's annoying that a double click is needed
        if event.type() == QEvent.MouseButtonRelease:
            print("ha!")
            return self.editorEvent(
                QEvent(QEvent.MouseButtonDblClick), model, option, index
            )
        elif event.type() == QEvent.MouseButtonRelease:
            print("double")
        else:
            print(f" its {event.type()}")

        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        opt = QStyleOptionComboBox()
        opt.rect = option.rect
        value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
        opt.currentText = value
        QApplication.style().drawComplexControl(QStyle.CC_ComboBox, opt, painter)
        opt = QStyleOptionComboBox()
        opt.rect = option.rect
        value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
        opt.currentText = value
        QApplication.style().drawControl(QStyle.CE_ComboBoxLabel, opt, painter)


class CatalogueCheckDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.MouseButtonRelease:
            value = (
                index.data(int(wizard_tools.SourceModel.Roles.IS_CATALOGUE)) or False
            )
            model.setData(
                index, not value, int(wizard_tools.SourceModel.Roles.IS_CATALOGUE)
            )
            return True
        return super().editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        opt = QStyleOptionButton()
        opt.rect = option.rect
        value = index.data(int(wizard_tools.SourceModel.Roles.IS_CATALOGUE)) or False
        opt.state |= QStyle.State_On if value else QStyle.State_Off
        QApplication.style().drawControl(QStyle.CE_CheckBox, opt, painter)


class ImportDataConfigurationPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self, parent)
        self.workflow_wizard = parent

        self.setupUi(self)
        self.setTitle(title)

        self.workflow_wizard = parent

        self.workflow_wizard.import_data_file_model.sourceModel().setHorizontalHeaderLabels(
            [self.tr("Import File"), self.tr("Cat"), self.tr("Dataset")]
        )
        self.file_table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.file_table_view.setModel(self.workflow_wizard.import_data_file_model)
        self.file_table_view.verticalHeader().setSectionsMovable(True)
        self.file_table_view.verticalHeader().setDragEnabled(True)
        self.file_table_view.verticalHeader().setDragDropMode(QHeaderView.InternalMove)
        self.file_table_view.resizeColumnsToContents()

        self.db_connector = None

        self.datasetmanager_dlg = None
        self.datasetmanager_button.setCheckable(True)
        self.datasetmanager_button.clicked.connect(self._show_datasetmanager_dialog)
        self.datasetmanager_button.setIcon(
            QIcon(
                os.path.join(
                    os.path.dirname(__file__),
                    "../../images/QgisModelBaker-datasetmanager-icon.svg",
                )
            )
        )

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
                index = self.workflow_wizard.import_data_file_model.index(row, 2)
                value = index.data(int(wizard_tools.SourceModel.Roles.DATASET_NAME))
                if not value:
                    self.workflow_wizard.import_data_file_model.setData(
                        index,
                        wizard_tools.DEFAULT_DATASETNAME,
                        int(wizard_tools.SourceModel.Roles.DATASET_NAME),
                    )

                self.file_table_view.setItemDelegateForColumn(
                    1, CatalogueCheckDelegate(self)
                )
                self.file_table_view.setItemDelegateForColumn(
                    2, DatasetComboDelegate(self, self.db_connector)
                )
        else:
            self.file_table_view.setColumnHidden(1, True)
            self.file_table_view.setColumnHidden(2, True)
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
            2, DatasetComboDelegate(self, self.db_connector)
        )
