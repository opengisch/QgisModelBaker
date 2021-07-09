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
    QStringListModel,
    QSortFilterProxyModel,
    Qt
)

from QgisModelBaker.libili2db.ilicache import IliCache

class SourceModel(QStandardItemModel):
    class Roles(Enum):
        NAME = Qt.UserRole + 1
        TYPE = Qt.UserRole + 2
        PATH = Qt.UserRole + 3
        DATASET_NAME = Qt.UserRole + 4

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def data(self, index , role):
        type_item = self.item(index.row(), 0)
        item = self.item(index.row(), 1)

        if role == Qt.DisplayRole:
            if type_item.data(int(SourceModel.Roles.TYPE)) != 'model':
                return self.tr('{} ({})').format(item.data(int(SourceModel.Roles.NAME)), item.data(int(SourceModel.Roles.PATH)))
        return item.data(int(role))

    def add_source(self, name, type, path):
        items = []
        item = QStandardItem()
        item.setData(type, int(SourceModel.Roles.TYPE))
        items.append(item)

        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(path, int(SourceModel.Roles.PATH))
        item.setData(QIcon(os.path.join(os.path.dirname(__file__), f'../images/file_types/{type}.png')), Qt.DecorationRole)
        items.append(item)

        self.appendRow(items)

    def remove_sources(self, indices):
        for index in sorted(indices):
            self.removeRow(index.row()) 

class ImportModelsModel(QStringListModel):

    blacklist = ['CHBaseEx_MapCatalogue_V1', 'CHBaseEx_WaterNet_V1', 'CHBaseEx_Sewage_V1', 'CHAdminCodes_V1',
                    'AdministrativeUnits_V1', 'AdministrativeUnitsCH_V1', 'WithOneState_V1',
                    'WithLatestModification_V1', 'WithModificationObjects_V1', 'GraphicCHLV03_V1', 'GraphicCHLV95_V1',
                    'NonVector_Base_V2', 'NonVector_Base_V3', 'NonVector_Base_LV03_V3_1', 'NonVector_Base_LV95_V3_1',
                    'GeometryCHLV03_V1', 'GeometryCHLV95_V1', 'InternationalCodes_V1', 'Localisation_V1',
                    'LocalisationCH_V1', 'Dictionaries_V1', 'DictionariesCH_V1', 'CatalogueObjects_V1',
                    'CatalogueObjectTrees_V1', 'AbstractSymbology', 'CodeISO', 'CoordSys', 'GM03_2_1Comprehensive',
                    'GM03_2_1Core', 'GM03_2Comprehensive', 'GM03_2Core', 'GM03Comprehensive', 'GM03Core',
                    'IliRepository09', 'IliSite09', 'IlisMeta07', 'IliVErrors', 'INTERLIS_ext', 'RoadsExdm2ben',
                    'RoadsExdm2ben_10', 'RoadsExgm2ien', 'RoadsExgm2ien_10', 'StandardSymbology', 'StandardSymbology',
                    'Time', 'Units']

    def __init__(self):
        super().__init__()
        self._checked_models = None
    
    def collect_models(self, filtered_source_model, db_connector=None):
        modelnames = list()
        
        ili_file_paths = []
        filtered_source_model.setFilterFixedString('ili')
        for r in range(0,filtered_source_model.rowCount()):
            index = filtered_source_model.index(r,1)
            ili_file_paths.append(index.data(int(SourceModel.Roles.PATH)))

        for ili_file_path in ili_file_paths:
            self.ilicache = IliCache(None, ili_file_path)
            models = self.ilicache.process_ili_file(ili_file_path)
            print(f"models of {ili_file_path} are {models}")
               
        '''
            try:
                self.ili_models_line_edit.setText(models[-1]['name'])
                self.ili_models_line_edit.setPlaceholderText(models[-1]['name'])
            except IndexError:
                    self.ili_models_line_edit.setText('')
                    self.ili_models_line_edit.setPlaceholderText(self.tr('[No models found in ili file]'))


        get models from source_model
        
        db_models = self.db_models(db_connector)
        
        if modelname not in db_models:
            modelnames.append(modelname) 
        self.setStringList(modelnames)
        '''

    def db_models(self, db_connector=None):
        modelnames = list()
        
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r'(?:\{[^\}]*\}|\s)')
                    for modelname in regex.split(db_model['modelname']):
                        if modelname and modelname not in ExportModels.blacklist:
                            modelnames.append(modelname.strip())

        self.db_models(modelnames)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            return self._checked_models[self.data(index, Qt.DisplayRole)]
        else:
            return QStringListModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self._checked_models[self.data(index, Qt.DisplayRole)] = data
        else:
            QStringListModel.setData(self, index, role, data)

    def check(self, index):
        if self.data(index, Qt.CheckStateRole) == Qt.Checked:
            self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
        else:
            self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def checked_models(self):
        return [modelname for modelname in self.stringList() if self._checked_models[modelname] == Qt.Checked]

class ImportWizard (QWizard):

    Page_Intro = 1
    Page_ImportSourceSeletion = 2
    Page_ImportDatabaseSelection = 3
    Page_ImportSchemaConfiguration = 4
    Page_ImportDataConfigurtation = 5

    def __init__(self, base_config, parent=None):
        QWizard.__init__(self)

        self.source_model = SourceModel()
        self.file_model = QSortFilterProxyModel()
        self.file_model.setSourceModel(self.source_model)
        #maybe we can use here filter row and wont need to make multiple columnds...
        self.file_model.setFilterKeyColumn(0) 
        self.import_models_model = ImportModelsModel()
        self.source_model.rowsInserted.connect( lambda: self.refresh_import_models_model())
        self.source_model.rowsRemoved.connect( lambda: self.refresh_import_models_model())

        self.setPage(self.Page_Intro, IntroPage(self))
        self.setPage(self.Page_ImportSourceSeletion, ImportSourceSeletionPage(base_config, self))
        self.setPage(self.Page_ImportDatabaseSelection, ImportDatabaseSelectionPage(base_config, self))
        self.setPage(self.Page_ImportSchemaConfiguration, ImportSchemaConfigurationPage(base_config, self))
        #self.setPage(self.Page_ImportDataConfigurtation, ImportDataConfigurtationPage())

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"));
        self.setWizardStyle(QWizard.ModernStyle);

    def refresh_import_models_model(self):
        self.import_models_model.collect_models(self.file_model, None) 
