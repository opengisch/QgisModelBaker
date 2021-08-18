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

from PyQt5.uic.uiparser import _parse_alignment

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QHeaderView,
    QItemDelegate,
    QComboBox,
    QStyle,
    QStyleOptionComboBox,
    QApplication
)

from qgis.PyQt.QtCore import (
    Qt,
    QVariant,
    QAbstractTableModel
)

from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem
)


from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.gui.ili2db_options import Ili2dbOptionsDialog

from ...utils import get_ui_class

PAGE_UI = get_ui_class('workflow_wizard/import_data_configuration.ui')

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
        self.beginResetModel()
        self.clear()
        for record in datasets_info:
            item = QStandardItem()
            item.setData(record['datasetname'], int(Qt.DisplayRole))
            item.setData(record['datasetname'], int(DatasetSourceModel.Roles.DATASETNAME))
            item.setData(record['t_id'], int(DatasetSourceModel.Roles.TID))
            self.appendRow(item)
        self.endResetModel()
class Delegate(QItemDelegate):
    def __init__(self, owner, choices):
        super().__init__(owner)
        self.items = choices
    def createEditor(self, parent, option, index):
        self.editor = QComboBox(parent)
        self.editor.addItems(self.items)
        return self.editor
    def paint(self, painter, option, index):
        value = index.data(Qt.DisplayRole)
        style = QApplication.style()
        opt = QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
        QItemDelegate.paint(self, painter, option, index)
    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        num = self.items.index(value)
        editor.setCurrentIndex(num)
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, Qt.DisplayRole, QVariant(value))
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
class Model(QAbstractTableModel):
    def __init__(self, table):
        super().__init__()
        self.table = table
    def rowCount(self, parent):
        return len(self.table)
    def columnCount(self, parent):
        return len(self.table[0])
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.table[index.row()][index.column()]
    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self.table[index.row()][index.column()] = value
        return True

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
        
        # hide dataset column because not yet implemented
        # self.file_table_view.setColumnHidden(1,True)

        choices = ['apple', 'orange', 'banana']
        table = []
        table.append(['A', choices[0]])
        table.append(['B', choices[0]])
        table.append(['C', choices[0]])
        table.append(['D', choices[0]])
        # create table view:
        self.model = Model(table)
        self.file_table_view.setModel( self.model)
        
        self.file_table_view.setItemDelegateForColumn(1, Delegate(self,choices))
        # make combo boxes editable with a single-click:
        for row in range( len(table) ):
            self.file_table_view.openPersistentEditor(self.model.index(row, 1))


        self.ili2db_options = Ili2dbOptionsDialog()
        self.ili2db_options_button.clicked.connect(self.ili2db_options.open)
        self.ili2db_options.finished.connect(self.fill_toml_file_info_label)

    def order_list(self):
        order_list = []
        for visual_index in range(0, self.file_table_view.verticalHeader().count()):
            order_list.append(
                self.file_table_view.verticalHeader().logicalIndex(visual_index))
        return order_list

    def fill_toml_file_info_label(self):
        text = None
        if self.ili2db_options.toml_file():
            text = self.tr('Extra Model Information File: {}').format(('…'+self.ili2db_options.toml_file()[len(
                self.ili2db_options.toml_file())-40:]) if len(self.ili2db_options.toml_file()) > 40 else self.ili2db_options.toml_file())
        self.toml_file_info_label.setText(text)
        self.toml_file_info_label.setToolTip(self.ili2db_options.toml_file())

    def restore_configuration(self):
        # takes settings from QSettings and provides it to the gui (not the configuration)
        # since delete data should be turned off the only left thingy is the toml-file
        self.fill_toml_file_info_label()
        # set chk_delete_data always to unchecked because otherwise the user could delete the data accidentally
        self.chk_delete_data.setChecked(False)

    def update_configuration(self, configuration):
        # takes settings from the GUI and provides it to the configuration
        configuration.delete_data = self.chk_delete_data.isChecked()
        # ili2db_options
        configuration.inheritance = self.ili2db_options.inheritance_type()
        configuration.tomlfile = self.ili2db_options.toml_file()
        configuration.create_basket_col = self.ili2db_options.create_basket_col()
        configuration.create_import_tid = self.ili2db_options.create_import_tid()
        configuration.stroke_arcs = self.ili2db_options.stroke_arcs()
        configuration.pre_script = self.ili2db_options.pre_script()
        configuration.post_script = self.ili2db_options.post_script()

    def nextId(self):
        return self.workflow_wizard.next_id()
