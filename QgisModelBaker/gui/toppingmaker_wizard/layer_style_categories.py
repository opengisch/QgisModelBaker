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

from qgis.core import QgsApplication, QgsMapLayer
from qgis.PyQt.QtCore import QAbstractListModel, Qt
from qgis.PyQt.QtWidgets import QDialog

from QgisModelBaker.utils import gui_utils

DIALOG_UI = gui_utils.get_ui_class("toppingmaker_wizard/layer_style_categories.ui")


class LayerStyleCategoriesModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        # - [ ] make diffference between layer like in QgsMapLayerStyleCategoriesModel and make auswahl of categories accordingly
        # - [ ] option for all categories
        self.category_list = [
            QgsMapLayer.StyleCategory.LayerConfiguration,
            QgsMapLayer.StyleCategory.Symbology,
            QgsMapLayer.StyleCategory.Symbology3D,
            QgsMapLayer.StyleCategory.Labeling,
            QgsMapLayer.StyleCategory.Fields,
            QgsMapLayer.StyleCategory.Forms,
            QgsMapLayer.StyleCategory.Actions,
            QgsMapLayer.StyleCategory.MapTips,
            QgsMapLayer.StyleCategory.Diagrams,
            QgsMapLayer.StyleCategory.AttributeTable,
            QgsMapLayer.StyleCategory.Rendering,
            QgsMapLayer.StyleCategory.CustomProperties,
            QgsMapLayer.StyleCategory.GeometryOptions,
            QgsMapLayer.StyleCategory.Relations,
            QgsMapLayer.StyleCategory.Temporal,
            QgsMapLayer.StyleCategory.Legend,
            QgsMapLayer.StyleCategory.Elevation,
            QgsMapLayer.StyleCategory.Notes,
        ]
        self.categories = QgsMapLayer.StyleCategories()
        print(self.category_list)

    def flags(self, index):
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

    def rowCount(self, parent) -> int:
        return len(self.category_list)

    def columnCount(self, parent) -> int:
        return 1

    def data(self, index, role):
        category = self.category_list[index.row()]

        if role == Qt.UserRole:
            return category
        if role == Qt.CheckStateRole:
            return Qt.Checked if self.categories & category else Qt.Unchecked
        if category == QgsMapLayer.StyleCategory.LayerConfiguration:
            if role == Qt.DisplayRole:
                return self.tr("Layer Configuration")
            if role == Qt.ToolTipRole:
                return self.tr(
                    "Identifiable, removable, searchable, display expression, read-only, hidden"
                )
            if role == Qt.DecorationRole:
                return QgsApplication.getThemeIcon("/propertyicons/system.svg")
        if category == QgsMapLayer.StyleCategory.Symbology:
            if role == Qt.DisplayRole:
                return self.tr("Symbology")
            if role == Qt.ToolTipRole:
                return None
            if role == Qt.DecorationRole:
                return QgsApplication.getThemeIcon("/propertyicons/symbology.svg")
        if category == QgsMapLayer.StyleCategory.Symbology3D:
            if role == Qt.DisplayRole:
                return self.tr("3D Symbology")
            if role == Qt.ToolTipRole:
                return None
            if role == Qt.DecorationRole:
                return QgsApplication.getThemeIcon("/3d.svg")

        return super().data(index, role)

    """
    case QgsMapLayer::StyleCategory::Labeling:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Labels" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/labels.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::Fields:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Fields" );
        case Qt::ToolTipRole:
          return tr( "Aliases, widgets, WMS/WFS, expressions, constraints, virtual fields" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/mSourceFields.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::Forms:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Forms" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/mActionFormView.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::Actions:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Actions" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/action.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::MapTips:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Map Tips" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/display.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::Diagrams:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Diagrams" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/diagram.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::AttributeTable:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Attribute Table Settings" );
        case Qt::ToolTipRole:
          return tr( "Choice and order of columns, conditional styling" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/mActionOpenTable.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::Rendering:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Rendering" );
        case Qt::ToolTipRole:
          return tr( "Scale visibility, simplify method, opacity" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/rendering.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::CustomProperties:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Custom Properties" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/mActionOptions.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::GeometryOptions:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Geometry Options" );
        case Qt::ToolTipRole:
          return tr( "Geometry constraints and validity checks" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/digitizing.svg" ) );
      }
      break;
    case QgsMapLayer::StyleCategory::Relations:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Relations" );
        case Qt::ToolTipRole:
          return tr( "Relations with other layers" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/relations.svg" ) );
      }
      break;

    case QgsMapLayer::StyleCategory::Temporal:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Temporal Properties" );
        case Qt::ToolTipRole:
          return tr( "Temporal properties" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/propertyicons/temporal.svg" ) );
      }
      break;

    case QgsMapLayer::StyleCategory::Legend:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Legend Settings" );
        case Qt::ToolTipRole:
          return tr( "Legend settings" );
        case Qt::DecorationRole:
          return QgsApplication::getThemeIcon( QStringLiteral( "/legend.svg" ) );
      }
      break;

    case QgsMapLayer::StyleCategory::Elevation:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "Elevation Properties" );
        case Qt::ToolTipRole:
          return tr( "Elevation properties" );
        case Qt::DecorationRole:
          return QIcon(); // TODO
      }
      break;

    case QgsMapLayer::StyleCategory::Notes:
      switch ( role )
      {
        case Qt::DisplayRole:
        case Qt::ToolTipRole:
          return tr( "Notes" );
        case Qt::DecorationRole:
          return QIcon(); // TODO
      }
      break;

    case QgsMapLayer::StyleCategory::AllStyleCategories:
      switch ( role )
      {
        case Qt::DisplayRole:
          return tr( "All Style Categories" );
        case Qt::ToolTipRole:
          return QVariant();
        case Qt::DecorationRole:
          return QVariant();
      }
      break;

  }
"""

    def setData(self, index, value, role) -> bool:
        if role == Qt.CheckState:
            category = self.data(index, Qt.UserRole)
            if value == Qt.Checked:
                self.categories |= category
                return True
            elif value == Qt.Unchecked:
                self.categories &= ~category
                return True
            return False
        return super().setData(index, value, role)

    def set_categories(self, categories: QgsMapLayer.StyleCategories):
        self.categories = categories


class LayerStyleCategoriesDialog(QDialog, DIALOG_UI):
    def __init__(self, categories: QgsMapLayer.StyleCategories, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        model = LayerStyleCategoriesModel()
        model.set_categories(categories)
        self.style_categories_list_view.setModel(model)
