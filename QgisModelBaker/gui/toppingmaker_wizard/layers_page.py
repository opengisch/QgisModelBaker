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

from qgis.core import (
    QgsApplication,
    QgsLayerTree,
    QgsLayerTreeModel,
    QgsMapLayer,
    QgsProject,
)
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QSizePolicy,
    QStyledItemDelegate,
    QToolButton,
    QWidget,
    QWizardPage,
)

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.gui.toppingmaker_wizard.layer_style_categories import (
    LayerStyleCategoriesDialog,
)
from QgisModelBaker.internal_libs.projecttopping.projecttopping import ExportSettings
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/layers.ui")


from enum import IntEnum

from qgis.PyQt.QtCore import Qt


class LayerStyleWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.checkbox = QCheckBox()
        self.settings_button = QToolButton()
        self.settings_button.setIcon(QgsApplication.getThemeIcon("/symbologyEdit.svg"))
        self.settings_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.settings_button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)


class StyleCatDelegate(QStyledItemDelegate):
    # buttonClicked = pyqtSignal(QtCore.QModelIndex, int)

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        self.editor = LayerStyleWidget(parent)
        self.editor.setAutoFillBackground(True)
        return self.editor

    def setEditorData(self, editor, index):
        check_state = index.data(Qt.CheckStateRole)
        if check_state is not None:
            self.editor.checkbox.setVisible(True)
            self.editor.settings_button.setVisible(True)
            self.editor.checkbox.setCheckState(check_state)
        else:
            self.editor.checkbox.setVisible(False)
            self.editor.settings_button.setVisible(False)

        # pass testwise all cats instead of categories = index.data(StyleCats)
        self.editor.settings_button.clicked.connect(
            lambda index: self.open_categories(index)
        )

    def open_categories(self, index):
        categories = QgsMapLayer.StyleCategory.AllStyleCategories
        categories_dialog = LayerStyleCategoriesDialog(categories)
        categories_dialog.exec_()

    def setModelData(self, editor, model, index):
        model.setData(index, self.editor.checkbox.checkState, Qt.CheckStateRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        self.parent().openPersistentEditor(index)


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

    def __init__(self, layertree: QgsLayerTree, export_settings=ExportSettings()):
        super().__init__(layertree)
        self.export_settings = export_settings
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
            node = self.index2node(index)
            if node:
                if (
                    index.column() == LayerModel.Columns.USE_STYLE
                    and not QgsLayerTree.isGroup(node)
                ):
                    settings = self.export_settings.get_setting(
                        ExportSettings.ToppingType.QMLSTYLE, node
                    )
                    return Qt.Checked if settings.get("export", False) else Qt.Unchecked
                if index.column() == LayerModel.Columns.USE_DEFINITION:
                    settings = self.export_settings.get_setting(
                        ExportSettings.ToppingType.DEFINITION, node
                    )
                    return Qt.Checked if settings.get("export", False) else Qt.Unchecked
                if (
                    index.column() == LayerModel.Columns.USE_SOURCE
                    and not QgsLayerTree.isGroup(node)
                ):
                    settings = self.export_settings.get_setting(
                        ExportSettings.ToppingType.SOURCE, node
                    )
                    return Qt.Checked if settings.get("export", False) else Qt.Unchecked

        if index.column() == LayerModel.Columns.NAME:
            return QgsLayerTreeModel.data(self, index, role)

        return None

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            node = self.index2node(index)
            if node:
                if (
                    index.column() == LayerModel.Columns.USE_STYLE
                    and not QgsLayerTree.isGroup(node)
                ):
                    self.export_settings.set_setting_values(
                        ExportSettings.ToppingType.QMLSTYLE,
                        node,
                        None,
                        bool(data),
                    )
                if index.column() == LayerModel.Columns.USE_DEFINITION:
                    self.export_settings.set_setting_values(
                        ExportSettings.ToppingType.DEFINITION,
                        node,
                        None,
                        bool(data),
                    )
                if (
                    index.column() == LayerModel.Columns.USE_SOURCE
                    and not QgsLayerTree.isGroup(node)
                ):
                    self.export_settings.set_setting_values(
                        ExportSettings.ToppingType.SOURCE,
                        node,
                        None,
                        bool(data),
                    )
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

        self.layermodel = LayerModel(
            QgsProject.instance().layerTreeRoot(),
            self.toppingmaker_wizard.topping_maker.exportsettings,
        )
        self.layermodel.setFlags(QgsLayerTreeModel.Flags())
        self.layer_table_view.setModel(self.layermodel)
        self.layer_table_view.resizeColumnToContents(LayerModel.Columns.NAME)
        self.layer_table_view.expandAll()
        self.layer_table_view.clicked.connect(self.layer_table_view.model().check)

        self.stylecat_delegate_button = StyleCatDelegate(self.layer_table_view)
        self.layer_table_view.setItemDelegateForColumn(
            LayerModel.Columns.USE_STYLE, self.stylecat_delegate_button
        )

        """
        - [ ] categories!
        - [ ] maybe the model should be in topping_maker or the values should go there on validatePage
        - [ ] ot the model should be in the topping_maker_wizard...
        - [ ] default values on raster -> source on vector -> qml etc.
        - [ ] could be finetuned a lot - like eg. when definition of group is selected the childs are disabled
        - [ ] colors to define what kind of layer it is
        """

    def initializePage(self) -> None:
        return super().initializePage()

    def validatePage(self) -> bool:
        return super().validatePage()
