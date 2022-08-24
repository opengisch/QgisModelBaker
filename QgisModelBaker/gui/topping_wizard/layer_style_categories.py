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

from qgis.core import QgsMapLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog

from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("topping_wizard/layer_style_categories.ui")


class LayerStyleCategoriesModel(gui_utils.CheckEntriesModel):

    CATEGORY_MAP = {
        "LayerConfiguration": QgsMapLayer.StyleCategory.LayerConfiguration,
        "Symbology": QgsMapLayer.StyleCategory.Symbology,
        "3D Symbology": QgsMapLayer.StyleCategory.Symbology3D,
        "Labeling": QgsMapLayer.StyleCategory.Labeling,
        "Fields": QgsMapLayer.StyleCategory.Fields,
        "Forms": QgsMapLayer.StyleCategory.Forms,
        "Actions": QgsMapLayer.StyleCategory.Actions,
        "Map Tips": QgsMapLayer.StyleCategory.MapTips,
        "Diagrams": QgsMapLayer.StyleCategory.Diagrams,
        "Attribute Table Settings": QgsMapLayer.StyleCategory.AttributeTable,
        "Rendering": QgsMapLayer.StyleCategory.Rendering,
        "Custom Properties": QgsMapLayer.StyleCategory.CustomProperties,
        "Geometry Options": QgsMapLayer.StyleCategory.GeometryOptions,
        "Relations": QgsMapLayer.StyleCategory.Relations,
        "Temporal": QgsMapLayer.StyleCategory.Temporal,
        "Legend": QgsMapLayer.StyleCategory.Legend,
        "Elevation": QgsMapLayer.StyleCategory.Elevation,
        "Notes": QgsMapLayer.StyleCategory.Notes,
    }

    def __init__(self):
        super().__init__()
        self.setStringList(LayerStyleCategoriesModel.CATEGORY_MAP.keys())

    def set_categories(self, categories: QgsMapLayer.StyleCategories):
        self.beginResetModel()
        self._checked_entries = {}
        for category_name in LayerStyleCategoriesModel.CATEGORY_MAP.keys():
            self._checked_entries[category_name] = (
                Qt.Checked
                if categories & LayerStyleCategoriesModel.CATEGORY_MAP[category_name]
                else Qt.Unchecked
            )
        self.endResetModel()

    def categories(self):
        categories = 0
        for name in self._checked_entries.keys():
            if self._checked_entries[name] == Qt.Checked:
                categories |= LayerStyleCategoriesModel.CATEGORY_MAP[name]
        return categories


class LayerStyleCategoriesDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.model = LayerStyleCategoriesModel()
        self.style_categories_list_view.setModel(self.model)
        self.style_categories_list_view.clicked.connect(
            self.style_categories_list_view.model().check
        )
        self.style_categories_list_view.space_pressed.connect(
            self.style_categories_list_view.model().check
        )

        self.ok_button.clicked.connect(self.accept)

    def set_categories(self, categories: QgsMapLayer.StyleCategories):
        self.style_categories_list_view.model().set_categories(categories)

    @property
    def categories(self):
        return self.style_categories_list_view.model().categories()
