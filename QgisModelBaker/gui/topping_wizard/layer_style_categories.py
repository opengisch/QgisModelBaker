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
from qgis.PyQt.QtCore import QAbstractListModel, Qt
from qgis.PyQt.QtWidgets import QDialog

from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("topping_wizard/layer_style_categories.ui")


class LayerStyleCategoriesModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        # - [ ] make diffference between layer like in QgsMapLayerStyleCategoriesModel and make auswahl of categories accordingly
        # - [ ] finalize the display of tooltip and icon
        # - [ ] solve time lag (maybe make StandardItemModel or store checked state not with flags...)

        self.category_list = [
            {
                "category": QgsMapLayer.StyleCategory.LayerConfiguration,
                "name": "LayerConfiguration",
                "icon": "",
                "icon": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Symbology,
                "name": "Symbology",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Symbology3D,
                "name": "3D Symbology",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Labeling,
                "name": "Labeling",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Fields,
                "name": "Fields",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Forms,
                "name": "Forms",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Actions,
                "name": "Actions",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.MapTips,
                "name": "Map Tips",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Diagrams,
                "name": "Diagrams",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.AttributeTable,
                "name": "Attribute Table Settings",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Rendering,
                "name": "Rendering",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.CustomProperties,
                "name": "Custom Properties",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.GeometryOptions,
                "name": "Geometry Options",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Relations,
                "name": "Relations",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Temporal,
                "name": "Temporal",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Legend,
                "name": "Legend",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Elevation,
                "name": "Elevation",
                "icon": "",
                "tooltip": "",
            },
            {
                "category": QgsMapLayer.StyleCategory.Notes,
                "name": "Notes",
                "icon": "",
                "tooltip": "",
            },
        ]
        self.categories = QgsMapLayer.StyleCategory.AllStyleCategories

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def rowCount(self, parent) -> int:
        return len(self.category_list)

    def columnCount(self, parent) -> int:
        return 1

    def data(self, index, role):
        category = self.category_list[index.row()]["category"]
        name = self.category_list[index.row()]["name"]

        if role == Qt.CheckStateRole:
            return Qt.Checked if self.categories & category else Qt.Unchecked
        if role == Qt.DisplayRole:
            return name

        return super().data(index, role)
        """
        if role == Qt.DisplayRole:
            if category == QgsMapLayer.StyleCategory.LayerConfiguration:
                return self.tr("Layer Configuration")
            if category == QgsMapLayer.StyleCategory.Symbology:
                return self.tr("Symbology")
            if category == QgsMapLayer.StyleCategory.Symbology3D:
                return self.tr("3D Symbology")
            if category == QgsMapLayer.StyleCategory.Labeling:
                return self.tr("Labels")
            if category == QgsMapLayer.StyleCategory.Fields:
                return self.tr("Fields")
            if category == QgsMapLayer.StyleCategory.Forms:
                return self.tr("Forms")
            if category == QgsMapLayer.StyleCategory.Actions:
                return self.tr("Actions")
            if category == QgsMapLayer.StyleCategory.MapTips:
                return self.tr("Map Tips")
            if category == QgsMapLayer.StyleCategory.Diagrams:
                return self.tr("Diagrams")
            if category == QgsMapLayer.StyleCategory.AttributeTable:
                return self.tr("Attribute Table Settings")
            if category == QgsMapLayer.StyleCategory.Rendering:
                return self.tr("Rendering")
            if category == QgsMapLayer.StyleCategory.CustomProperties:
                return self.tr( "Custom Properties" )
            if category == QgsMapLayer.StyleCategory.GeometryOptions:
                return self.tr( "Geometry Options" )
            if category == QgsMapLayer.StyleCategory.Relations:
                return self.tr( "Relations" )
            if category == QgsMapLayer.StyleCategory.CustomProperties:
                return self.tr( "Custom Properties" )
            if category == QgsMapLayer.StyleCategory.GeometryOptions:
                return self.tr( "Geometry Options" )
            if category == QgsMapLayer.StyleCategory.Relations:
                return self.tr( "Relations" )

        if role == Qt.DecorationRole:
            if category == QgsMapLayer.StyleCategory.LayerConfiguration:
                return QgsApplication.getThemeIcon("/propertyicons/system.svg")
            if category == QgsMapLayer.StyleCategory.Symbology:
                return QgsApplication.getThemeIcon("/propertyicons/symbology.svg")
            if category == QgsMapLayer.StyleCategory.Symbology3D:
                return QgsApplication.getThemeIcon("/3d.svg")
            if category == QgsMapLayer.StyleCategory.Labeling:
                return QgsApplication.getThemeIcon("/propertyicons/labels.svg")
            if category == QgsMapLayer.StyleCategory.Fields:
                return QgsApplication.getThemeIcon("/mSourceFields.svg")
            if category == QgsMapLayer.StyleCategory.Forms:
                return QgsApplication.getThemeIcon("/mActionFormView.svg")
            if category == QgsMapLayer.StyleCategory.Actions:
                return QgsApplication.getThemeIcon("/propertyicons/action.svg")
            if category == QgsMapLayer.StyleCategory.MapTips:
                return QgsApplication.getThemeIcon("/propertyicons/display.svg")
            if category == QgsMapLayer.StyleCategory.Diagrams:
                return QgsApplication.getThemeIcon("/propertyicons/diagram.svg")
            if category == QgsMapLayer.StyleCategory.AttributeTable:
                return QgsApplication.getThemeIcon("/mActionOpenTable.svg")
            if category == QgsMapLayer.StyleCategory.Rendering:
                return QgsApplication.getThemeIcon("/propertyicons/rendering.svg")
            if category == QgsMapLayer.StyleCategory.CustomProperties:
                return QgsApplication.getThemeIcon("/mActionOptions.svg")
            if category == QgsMapLayer.StyleCategory.GeometryOptions:
                return QgsApplication.getThemeIcon("/propertyicons/digitizing.svg")
            if category == QgsMapLayer.StyleCategory.Relations:
                return QgsApplication.getThemeIcon("/propertyicons/relations.svg")

        if role == Qt.ToolTipRole:
            if category == QgsMapLayer.StyleCategory.LayerConfiguration:
                return self.tr(
                    "Identifiable, removable, searchable, display expression, read-only, hidden"
                )
            if category == QgsMapLayer.StyleCategory.Symbology:
                return self.tr("Symbology")
            if category == QgsMapLayer.StyleCategory.Symbology3D:
                return self.tr("3D Symbology")
            if category == QgsMapLayer.StyleCategory.Labeling:
                return self.tr("Labels")
            if category == QgsMapLayer.StyleCategory.Fields:
                return self.tr( "Aliases, widgets, WMS/WFS, expressions, constraints, virtual fields" )
            if category == QgsMapLayer.StyleCategory.Forms:
                return self.tr("Forms")
            if category == QgsMapLayer.StyleCategory.Actions:
                return self.tr("Actions")
            if category == QgsMapLayer.StyleCategory.MapTips:
                return self.tr("Map Tips")
            if category == QgsMapLayer.StyleCategory.Diagrams:
                return self.tr("Diagrams")
            if category == QgsMapLayer.StyleCategory.AttributeTable:
                return self.tr( "Choice and order of columns, conditional styling" )
            if category == QgsMapLayer.StyleCategory.Rendering:
                return self.tr( "Scale visibility, simplify method, opacity" )
            if category == QgsMapLayer.StyleCategory.CustomProperties:
                return self.tr( "Custom Properties" )
            if category == QgsMapLayer.StyleCategory.GeometryOptions:
                return self.tr( "Geometry constraints and validity checks" )
            if category == QgsMapLayer.StyleCategory.Relations:
                return self.tr( "Relations with other layers" )
        """
        """
            if category == QgsMapLayer.StyleCategory.Temporal:
                return self.tr("Temporal Properties")
                if role == Qt.ToolTipRole:
                    return self.tr( "Temporal Properties" )
                if role == Qt.DecorationRole:
                    return QgsApplication.getThemeIcon("/propertyicons/temporal.svg")
            if category == QgsMapLayer.StyleCategory.Legend:
                return self.tr("Legend Settings")
                if role == Qt.ToolTipRole:
                    return self.tr("Legend Settings")
                if role == Qt.DecorationRole:
                    return QgsApplication.getThemeIcon("/legend.svg")
            if category == QgsMapLayer.StyleCategory.Legend:
                return self.tr("Elevation Properties")
                if role == Qt.ToolTipRole:
                    return self.tr("Elevation Properties")
                if role == Qt.DecorationRole:
                    return None
            if category == QgsMapLayer.StyleCategory.Notes:
                return self.tr("Notes")
                if role == Qt.ToolTipRole:
                    return self.tr("Notes")
                if role == Qt.DecorationRole:
                    return None
            if category == QgsMapLayer.StyleCategory.AllStyleCategories:
                return self.tr("All Style Categories")
                if role == Qt.ToolTipRole:
                    return self.tr("All Style Categories")
                if role == Qt.DecorationRole:
                return None
        """

    def setData(self, index, value, role) -> bool:
        if role == Qt.CheckStateRole:
            category = self.category_list[index.row()]["category"]
            if value == Qt.Checked:
                self.categories |= category
                self.dataChanged.emit(index, index)
                return True
            elif value == Qt.Unchecked:
                self.categories &= ~category
                self.dataChanged.emit(index, index)
                return True
            return False
        return super().setData(index, value, role)

    def set_categories(self, categories: QgsMapLayer.StyleCategories):
        self.beginResetModel()
        self.categories = categories
        self.endResetModel()


class LayerStyleCategoriesDialog(QDialog, DIALOG_UI):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.model = LayerStyleCategoriesModel()
        self.style_categories_list_view.setModel(self.model)

        self.ok_button.clicked.connect(self.accept)

    def set_categories(self, categories: QgsMapLayer.StyleCategories):
        self.model.set_categories(categories)

    @property
    def categories(self):
        return self.model.categories
