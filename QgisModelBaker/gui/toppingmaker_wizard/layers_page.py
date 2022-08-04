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

from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QWizardPage

import QgisModelBaker.utils.gui_utils as gui_utils
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("toppingmaker_wizard/layers.ui")


from enum import Enum, IntEnum

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QStandardItem, QStandardItemModel


# maybe this model should be in ProjectTopping or at least ToppingMaker
class LayerModel(QStandardItemModel):
    """
    Model providing the layers
    """

    class Roles(Enum):
        NAME = Qt.UserRole + 1
        PROVIDER = Qt.UserRole + 2
        USE_SOURCE = Qt.UserRole + 3
        USE_STYLE = Qt.UserRole + 5
        USE_DEFINITION = Qt.UserRole + 6

    def __int__(self):
        return self.value

    class Columns(IntEnum):
        NAME = 0
        USE_STYLE = 1
        USE_SOURCE = 2
        USE_DEFINITION = 3

    def __init__(self):
        super().__init__()
        self.setColumnCount(4)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        item = self.item(index.row(), index.column())
        if item:
            if role == Qt.DisplayRole:
                if index.column() == SourceModel.Columns.SOURCE:
                    return "{}{}".format(
                        item.data(int(Qt.DisplayRole)),
                        f" ({item.data(int(SourceModel.Roles.PATH))})"
                        if item.data(int(SourceModel.Roles.TYPE)) != "model"
                        else "",
                    )
                if index.column() == SourceModel.Columns.DATASET:
                    if self.index(index.row(), SourceModel.Columns.IS_CATALOGUE).data(
                        int(SourceModel.Roles.IS_CATALOGUE)
                    ):
                        return "---"
                    else:
                        return item.data(int(SourceModel.Roles.DATASET_NAME))

            if role == Qt.DecorationRole:
                if index.column() == SourceModel.Columns.SOURCE:
                    type = "data"
                    if item.data(int(SourceModel.Roles.TYPE)) and item.data(
                        int(SourceModel.Roles.TYPE)
                    ).lower() in ["model", "ili", "xtf", "xml"]:
                        type = item.data(int(SourceModel.Roles.TYPE)).lower()
                    return QIcon(
                        os.path.join(
                            os.path.dirname(__file__),
                            f"../images/file_types/{type}.png",
                        )
                    )
            return item.data(int(role))

    def add_layer(self, name, provider, use_source, use_style, use_definition):
        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(Roles.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        item.setData(origin_info, int(SourceModel.Roles.ORIGIN_INFO))
        self.appendRow([item, QStandardItem()])

        self.print_info.emit(
            self.tr("Add source {} ({}) {}").format(
                name, path if path else "repository", origin_info
            )
        )
        return True

    def setData(self, index, data, role):
        if index.column() == SourceModel.Columns.IS_CATALOGUE:
            return QStandardItemModel.setData(
                self, index, data, int(SourceModel.Roles.IS_CATALOGUE)
            )
        if index.column() == SourceModel.Columns.DATASET:
            return QStandardItemModel.setData(
                self, index, data, int(SourceModel.Roles.DATASET_NAME)
            )
        return QStandardItemModel.setData(self, index, data, role)

    def remove_sources(self, indices):
        for index in sorted(indices):
            path = index.data(int(SourceModel.Roles.PATH))
            self.print_info.emit(
                self.tr("Remove source {} ({})").format(
                    index.data(int(SourceModel.Roles.NAME)),
                    path if path else "repository",
                )
            )
            self.removeRow(index.row())

    def _source_in_model(self, name, type, path):
        match_existing = self.match(
            self.index(0, 0), int(SourceModel.Roles.NAME), name, -1, Qt.MatchExactly
        )
        if (
            match_existing
            and type == match_existing[0].data(int(SourceModel.Roles.TYPE))
            and path == match_existing[0].data(int(SourceModel.Roles.PATH))
        ):
            return True
        return False


class LayersPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title):
        QWizardPage.__init__(self)

        self.toppingmaker_wizard = parent

        self.setupUi(self)

        self.setTitle(title)

        self.layer_table_view.setModel(
            self.topping_wizard.topping_maker.project_topping.model
        )

    def initializePage(self) -> None:
        self.toppingmaker_wizard.topping_maker.create_projecttopping(
            QgsProject.instance()
        )
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
