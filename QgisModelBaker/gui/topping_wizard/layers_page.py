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


from enum import IntEnum

from qgis.core import (
    QgsApplication,
    QgsLayerTree,
    QgsLayerTreeLayer,
    QgsLayerTreeModel,
    QgsMapLayer,
    QgsProject,
)
from qgis.PyQt.QtCore import QModelIndex, Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor, QPalette
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QStyledItemDelegate,
    QToolButton,
    QWidget,
    QWizardPage,
)

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.gui.topping_wizard.layer_style_categories import (
    LayerStyleCategoriesDialog,
)
from QgisModelBaker.libs.modelbaker.ilitoppingmaker import ExportSettings
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    Ili2DbCommandConfiguration,
)
from QgisModelBaker.libs.modelbaker.utils import db_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("topping_wizard/layers.ui")


class LayerStyleWidget(QWidget):
    """
    Widget to have in the layer style column.
    """

    def __init__(self, parent=None, rect=None):
        QWidget.__init__(self, parent)

        self.checkbox = QCheckBox()
        self.settings_button = QToolButton()
        if rect:
            self.settings_button.setMaximumHeight(rect.height())
            self.settings_button.setMaximumWidth(rect.height())
        self.settings_button.setIcon(
            QgsApplication.getThemeIcon("/propertyicons/symbology.svg")
        )
        self.settings_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.settings_button.setVisible(False)
        self.checkbox.stateChanged.connect(self.settings_button.setVisible)

        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.settings_button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)


class LayerModel(QgsLayerTreeModel):
    """
    Model providing the layer tree and the settings.
    """

    class Roles(IntEnum):
        CATEGORIES = Qt.UserRole + 1

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
        self.ili_schema_identificators = []

        self.reload()

    def columnCount(self, parent=None):
        return len(LayerModel.Columns)

    def flags(self, index):
        if index.column() == LayerModel.Columns.NAME:
            return Qt.ItemIsEnabled
        if index.column() == LayerModel.Columns.USE_DEFINITION:
            return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
        if index.column() == LayerModel.Columns.USE_STYLE:
            return Qt.ItemIsEnabled
        else:
            node = self.index2node(index)
            if not QgsLayerTree.isGroup(node):
                return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
            else:
                return Qt.NoItemFlags

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == LayerModel.Columns.NAME:
                return self.tr("Layers and Groups")
            if section == LayerModel.Columns.USE_STYLE:
                return self.tr("Style (QML)")
            if section == LayerModel.Columns.USE_DEFINITION:
                return self.tr("Definition (QLR)")
            if section == LayerModel.Columns.USE_SOURCE:
                return self.tr("Source")
        if orientation == Qt.Horizontal and role == Qt.ToolTipRole:
            if section == LayerModel.Columns.NAME:
                return self.tr(
                    "The layers/groups listed here will be stored the layertree in the project topping (YAML) file. To remove a layer or a group, remove it in your project."
                )
            if section == LayerModel.Columns.USE_STYLE:
                return self.tr(
                    "The layer's style (forms, symbology, variables etc.) will be stored into a QML file."
                )
            if section == LayerModel.Columns.USE_DEFINITION:
                return self.tr(
                    "The layer's/group's definition (complete layer incl. source) will be stored into a QLR file."
                )
            if section == LayerModel.Columns.USE_SOURCE:
                return self.tr(
                    "The layer's source (provider and uri) will be stored into the project topping (YAML) file directly."
                )
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

        if role == Qt.BackgroundRole:
            node = self.index2node(index)
            if QgsLayerTree.isGroup(node):
                return QColor(Qt.gray)
            else:
                layer = QgsProject.instance().mapLayersByName(node.name())[0]
                if layer:
                    if layer.type() == QgsMapLayer.VectorLayer:
                        if self._is_ili_schema(layer):
                            return QColor(gui_utils.BLUE)
                    return QColor(gui_utils.GREEN)

        if (
            role == LayerModel.Roles.CATEGORIES
            and index.column() == LayerModel.Columns.USE_STYLE
        ):
            node = self.index2node(index)
            if node:
                settings = self.export_settings.get_setting(
                    ExportSettings.ToppingType.QMLSTYLE, node
                )
                return settings.get(
                    "categories", QgsMapLayer.StyleCategory.AllStyleCategories
                )

        return QgsLayerTreeModel.data(self, index, role)

    # this is unusual that it's not first data and then role (could be changed)
    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            node = self.index2node(index)
            if node:
                if (
                    index.column() == LayerModel.Columns.USE_STYLE
                    and not QgsLayerTree.isGroup(node)
                ):
                    self._set_export_settings_values_for_all_styles(
                        ExportSettings.ToppingType.QMLSTYLE,
                        node,
                        None,
                        bool(data),
                    )

                    if bool(data):
                        # when the style or source get's checked, the definition become unchecked
                        self.export_settings.set_setting_values(
                            ExportSettings.ToppingType.DEFINITION,
                            node,
                            None,
                            False,
                        )

                        # when something is checked, the parent's definition become unchecked
                        self._disable_parent_definition(index)

                if index.column() == LayerModel.Columns.USE_DEFINITION:
                    self.export_settings.set_setting_values(
                        ExportSettings.ToppingType.DEFINITION,
                        node,
                        None,
                        bool(data),
                    )

                    if bool(data):
                        # when the definition is checked the others become unchecked
                        self._set_export_settings_values_for_all_styles(
                            ExportSettings.ToppingType.QMLSTYLE,
                            node,
                            None,
                            False,
                        )
                        self.export_settings.set_setting_values(
                            ExportSettings.ToppingType.SOURCE,
                            node,
                            None,
                            False,
                        )

                        # when something is checked, the parent's definition become unchecked
                        self._disable_parent_definition(index)

                        # when definition is checked, che children's columns become all unchecked
                        self._disable_children(index)
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
                    if bool(data):
                        # when the style or source get's checked, the definition become unchecked
                        self.export_settings.set_setting_values(
                            ExportSettings.ToppingType.DEFINITION,
                            node,
                            None,
                            False,
                        )

                        # when something is checked, the parent's definition become unchecked
                        self._disable_parent_definition(index)

                self.dataChanged.emit(
                    self.index(index.row(), 0),
                    self.index(index.row(), self.columnCount()),
                )
                return True

        if (
            role == LayerModel.Roles.CATEGORIES
            and index.column() == LayerModel.Columns.USE_STYLE
        ):
            node = self.index2node(index)
            if node:
                self._set_export_settings_values_for_all_styles(
                    ExportSettings.ToppingType.QMLSTYLE, node, None, True, data
                )
                return True

        return QgsLayerTreeModel.setData(self, index, role, data)

    def check(self, index):
        if index.flags() & (Qt.ItemIsUserCheckable | Qt.ItemIsEnabled):
            if self.data(index, Qt.CheckStateRole) == Qt.Checked:
                self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
            else:
                self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def reload(self):
        self._load_ili_schema_identificators()
        self._set_default_values()

    def _disable_children(self, parent: QModelIndex):
        for child_row in range(self.rowCount(parent)):
            self.setData(
                self.index(child_row, LayerModel.Columns.USE_STYLE, parent),
                Qt.CheckStateRole,
                False,
            )
            self.setData(
                self.index(child_row, LayerModel.Columns.USE_DEFINITION, parent),
                Qt.CheckStateRole,
                False,
            )
            self.setData(
                self.index(child_row, LayerModel.Columns.USE_SOURCE, parent),
                Qt.CheckStateRole,
                False,
            )
            self._disable_children(
                self.index(child_row, LayerModel.Columns.USE_DEFINITION, parent)
            )

    def _disable_parent_definition(self, index: QModelIndex):
        if index.parent() == QModelIndex():
            # parent of index is root
            return
        parent_definition_index = self.index(
            index.parent().row(),
            LayerModel.Columns.USE_DEFINITION,
            index.parent().parent(),
        )
        self.setData(parent_definition_index, Qt.CheckStateRole, False)
        if index.parent() != QModelIndex():
            self._disable_parent_definition(index.parent())

    def _load_ili_schema_identificators(self):
        """
        Checks all the layers if it's based on an interlis class.
        This is not done every time the layertree changes, so not realtime to have better performance.
        """
        self.ili_schema_identificators = []
        checked_schema_identificator = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.VectorLayer:
                source_provider = layer.dataProvider()
                schema_identificator = (
                    db_utils.get_schema_identificator_from_sourceprovider(
                        source_provider
                    )
                )
                if (
                    not schema_identificator
                    or schema_identificator in checked_schema_identificator
                ):
                    continue

                checked_schema_identificator.append(schema_identificator)
                configuration = Ili2DbCommandConfiguration()
                valid, mode = db_utils.get_configuration_from_sourceprovider(
                    source_provider, configuration
                )
                if valid and mode:
                    configuration.tool = mode
                    db_connector = db_utils.get_db_connector(configuration)

                    if (
                        db_connector
                        and db_connector.db_or_schema_exists()
                        and db_connector.metadata_exists()
                    ):
                        self.ili_schema_identificators.append(schema_identificator)

    def _is_ili_schema(self, layer):
        if not layer or not layer.dataProvider() or not layer.dataProvider().isValid():
            return False

        source_provider = layer.dataProvider()
        schema_identificator = db_utils.get_schema_identificator_from_sourceprovider(
            source_provider
        )
        return schema_identificator in self.ili_schema_identificators

    def _set_default_values(self):
        """
        Sets QMLSTYLE for vector layers from INTERLIS schema and the SOURCE for all the others.
        Groups are unset on default.
        """
        root = self.rootGroup()
        layernodes = root.findLayers()
        groupnodes = root.findGroups(True)

        self.beginResetModel()
        for layernode in layernodes:
            if self._is_ili_schema(layernode.layer()):
                self._set_export_settings_values_for_all_styles(
                    ExportSettings.ToppingType.QMLSTYLE,
                    layernode,
                    None,
                    bool(True),
                )
                self.export_settings.set_setting_values(
                    ExportSettings.ToppingType.DEFINITION,
                    layernode,
                    None,
                    bool(False),
                )
                self.export_settings.set_setting_values(
                    ExportSettings.ToppingType.SOURCE,
                    layernode,
                    None,
                    bool(False),
                )
            else:
                self._set_export_settings_values_for_all_styles(
                    ExportSettings.ToppingType.QMLSTYLE,
                    layernode,
                    None,
                    bool(False),
                )
                self.export_settings.set_setting_values(
                    ExportSettings.ToppingType.DEFINITION,
                    layernode,
                    None,
                    bool(False),
                )
                self.export_settings.set_setting_values(
                    ExportSettings.ToppingType.SOURCE,
                    layernode,
                    None,
                    bool(True),
                )
        for groupnode in groupnodes:
            self.export_settings.set_setting_values(
                ExportSettings.ToppingType.QMLSTYLE,
                groupnode,
                None,
                bool(False),
            )
            self.export_settings.set_setting_values(
                ExportSettings.ToppingType.DEFINITION,
                groupnode,
                None,
                bool(False),
            )
            self.export_settings.set_setting_values(
                ExportSettings.ToppingType.SOURCE,
                groupnode,
                None,
                bool(False),
            )
        self.endResetModel()

    def _set_export_settings_values_for_all_styles(
        self,
        type=ExportSettings.ToppingType.QMLSTYLE,
        node: QgsLayerTreeLayer = None,
        name: str = None,
        export=True,
        categories=None,
    ):
        """
        Currently individual settings per style is not supported by the exporter.
        So we have this function applying the setting (export True/False and category) on each style.
        """
        if isinstance(node, QgsLayerTreeLayer):
            for style_name in node.layer().styleManager().styles():
                self.export_settings.set_setting_values(
                    type, node, name, export, categories, style_name
                )


class StyleCatDelegate(QStyledItemDelegate):

    button_clicked = pyqtSignal(QModelIndex)

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        widget = LayerStyleWidget(parent, option.rect)
        widget.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Base, QColor(index.data(Qt.BackgroundRole)))
        widget.setPalette(palette)
        widget.checkbox.stateChanged.connect(
            lambda state: index.model().setData(index, Qt.CheckStateRole, state)
        )
        widget.settings_button.clicked.connect(lambda: self.button_clicked.emit(index))
        return widget

    def setEditorData(self, editor, index):
        check_state = index.data(Qt.CheckStateRole)
        if check_state is not None:
            editor.checkbox.setVisible(True)
            editor.checkbox.setCheckState(check_state)
        else:
            editor.checkbox.setVisible(False)
            editor.settings_button.setVisible(False)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        self.parent().openPersistentEditor(index)


class LayersPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.topping_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.layermodel = LayerModel(
            QgsProject.instance().layerTreeRoot(),
            self.topping_wizard.topping.export_settings,
        )
        self.layermodel.setFlags(QgsLayerTreeModel.Flags())
        self.layer_table_view.setModel(self.layermodel)
        self.layer_table_view.header().setSectionResizeMode(
            LayerModel.Columns.NAME, QHeaderView.Stretch
        )
        self.layer_table_view.header().setStretchLastSection(False)

        self.layer_table_view.expandAll()
        self.layer_table_view.clicked.connect(self.layer_table_view.model().check)

        self.stylecat_delegate = StyleCatDelegate(self.layer_table_view)
        self.layer_table_view.setItemDelegateForColumn(
            LayerModel.Columns.USE_STYLE, self.stylecat_delegate
        )

        self.categories_dialog = LayerStyleCategoriesDialog()
        self.stylecat_delegate.button_clicked.connect(self.open_categories_dialog)
        self.reset_button.clicked.connect(self.layermodel.reload)

    def open_categories_dialog(self, index):
        layername = index.data(int(Qt.DisplayRole))
        self.categories_dialog.setWindowTitle(
            self.tr(f"Layer Style Categories of {layername}")
        )
        categories = index.data(int(LayerModel.Roles.CATEGORIES))
        self.categories_dialog.set_categories(categories)
        if self.categories_dialog.exec_():
            self.layermodel.setData(
                index,
                int(LayerModel.Roles.CATEGORIES),
                self.categories_dialog.categories,
            )

    def initializePage(self) -> None:
        self.layermodel.export_settings = self.topping_wizard.topping.export_settings
        self.layermodel.reload()
        return super().initializePage()

    def validatePage(self) -> bool:
        self.topping_wizard.log_panel.print_info(
            self.tr("Set export settings for layers."),
            gui_utils.LogColor.COLOR_SUCCESS,
        )
        return super().validatePage()
