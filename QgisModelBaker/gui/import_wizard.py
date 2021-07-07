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
import os

from qgis.PyQt.QtWidgets import QWizard

from QgisModelBaker.gui.intro_page import IntroPage
from QgisModelBaker.gui.import_source_selection_page import ImportSourceSeletionPage
from QgisModelBaker.gui.import_database_selection_page import ImportDatabaseSelectionPage
from QgisModelBaker.gui.import_schema_configuration_page import ImportSchemaConfigurationPage

from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QIcon
)

from qgis.PyQt.QtCore import (
    Qt
)

class SourceModel(QStandardItemModel):
    class Roles(Enum):
        NAME = Qt.UserRole + 1
        TYPE = Qt.UserRole + 2
        PATH = Qt.UserRole + 3

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def data(self , index , role):
        if role == Qt.DisplayRole:
            if QStandardItemModel.data(self, index, int(SourceModel.Roles.TYPE)) != 'model':
                return self.tr('{} ({})'.format(QStandardItemModel.data(self, index, int(SourceModel.Roles.NAME)), QStandardItemModel.data(self, index, int(SourceModel.Roles.PATH))))
        return QStandardItemModel.data(self, index, role)

    def add_source(self, name, type, path):
        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        item.setData(QIcon(os.path.join(os.path.dirname(__file__), f'../images/file_types/{type}.png')), Qt.DecorationRole)
        self.appendRow(item)
    
    def remove_sources(self, indices):
        for index in sorted(indices):
            self.removeRow(index.row()) 

class ImportWizard (QWizard):

    Page_Intro = 1
    Page_ImportSourceSeletion = 2
    Page_ImportDatabaseSelection = 3
    Page_ImportSchemaConfiguration = 4
    Page_ImportDataConfigurtation = 5

    def __init__(self, base_config, parent=None):
        QWizard.__init__(self)

        self.source_model = SourceModel()

        self.setPage(self.Page_Intro, IntroPage(self))
        self.setPage(self.Page_ImportSourceSeletion, ImportSourceSeletionPage(base_config, self))
        self.setPage(self.Page_ImportDatabaseSelection, ImportDatabaseSelectionPage(base_config, self))
        self.setPage(self.Page_ImportSchemaConfiguration, ImportSchemaConfigurationPage(base_config, self))
        #self.setPage(self.Page_ImportDataConfigurtation, ImportDataConfigurtationPage())

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"));
        self.setWizardStyle(QWizard.ModernStyle);