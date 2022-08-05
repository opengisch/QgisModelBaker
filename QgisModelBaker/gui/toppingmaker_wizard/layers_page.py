# -*- coding: utf-8 -*-
"""
/***************************************************************************
                              -------------------
        begin                : 2022-08-01
        git sha              : :%H$
        copyright            : (C) 2022 by Dave Signer
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

from qgis.core import QgsLayerTree, QgsLayerTreeModel, QgsProject
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/layers.ui")


from enum import IntEnum

from qgis.PyQt.QtCore import Qt


# maybe this model should be in ProjectTopping or at least ToppingMaker
class LayerModel(QgsLayerTreeModel):
    """
    Model providing the layer tree and the settings
    """

    class Columns(IntEnum):
        NAME = 0
        USE_STYLE = 1
        USE_DEFINITION = 2
        USE_SOURCE = 3

    def __init__(self, layertree: QgsLayerTree):
        super().__init__(layertree)
        self.use_style_nodes = {}
        self.use_source_nodes = {}
        self.use_definition_nodes = {}

    def columnCount(self, parent):
        return len(LayerModel.Columns)

    def flags(self, index):
        if index.column() == LayerModel.Columns.NAME:
            return Qt.ItemIsEnabled
        if index.column() == LayerModel.Columns.USE_DEFINITION:
            return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        else:
            node = self.index2node(index)
            if not QgsLayerTree.isGroup(node):
                return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
            else:
                return Qt.NoItemFlags

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == LayerModel.Columns.NAME:
                return self.tr("Node")
            if section == LayerModel.Columns.USE_STYLE:
                return self.tr("Use Style")
            if section == LayerModel.Columns.USE_DEFINITION:
                return self.tr("Use Definition")
            if section == LayerModel.Columns.USE_SOURCE:
                return self.tr("Use Source")
        return QgsLayerTreeModel.headerData(self, section, orientation, role)

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            if self.index2node(index):
                if index.column() == LayerModel.Columns.USE_STYLE:
                    return self.use_style_nodes.get(
                        self.index2node(index), Qt.Unchecked
                    )
                if index.column() == LayerModel.Columns.USE_DEFINITION:
                    return self.use_definition_nodes.get(
                        self.index2node(index), Qt.Unchecked
                    )
                if index.column() == LayerModel.Columns.USE_SOURCE:
                    return self.use_source_nodes.get(
                        self.index2node(index), Qt.Unchecked
                    )
        if index.column() == LayerModel.Columns.NAME:
            return QgsLayerTreeModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            if self.index2node(index):
                if index.column() == LayerModel.Columns.USE_STYLE:
                    self.use_style_nodes[self.index2node(index)] = data
                if index.column() == LayerModel.Columns.USE_DEFINITION:
                    self.use_definition_nodes[self.index2node(index)] = data
                if index.column() == LayerModel.Columns.USE_SOURCE:
                    self.use_source_nodes[self.index2node(index)] = data
                self.dataChanged.emit(
                    self.index(0, 0),
                    self.index(self.rowCount(), self.columnCount(self.parent)),
                )
                return True
        return QgsLayerTreeModel.setData(self, index, role, data)

    def check(self, index):
        if index.flags() & (Qt.ItemIsUserCheckable | Qt.ItemIsEnabled):
            if self.data(index, Qt.CheckStateRole) == Qt.Checked:
                self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
            else:
                self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def _emit_data_changed(self):
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount(), self.columnCount(self.parent))
        )


class LayersPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.layermodel = LayerModel(QgsProject.instance().layerTreeRoot())
        self.layermodel.setFlags(QgsLayerTreeModel.Flags())
        self.layer_table_view.setModel(self.layermodel)
        self.layer_table_view.resizeColumnToContents(LayerModel.Columns.NAME)
        self.layer_table_view.expandAll()
        self.layer_table_view.clicked.connect(self.layer_table_view.model().check)

    def initializePage(self) -> None:
        return super().initializePage()

    def validatePage(self) -> bool:
        if not self.toppingmaker_wizard.topping_maker.models_model.checked_entries:
            self.toppingmaker_wizard.log_panel.print_info(
                self.tr("At least one model should be selected."),
                gui_utils.LogColor.COLOR_FAIL,
            )
            return False
        return super().validatePage()


# we need a model and we load here the topingmaker.projecttopping as a pointer and with this it's edited
