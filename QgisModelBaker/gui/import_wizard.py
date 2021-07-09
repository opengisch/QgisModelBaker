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
import re

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
    QSortFilterProxyModel,
    QTimer,
    Qt
)

from QgisModelBaker.libili2db.ilicache import IliCache

# dave put them all to the same place
IliExtensions = ['ili']
TransferExtensions = ['xtf', 'XTF', 'itf', 'ITF', 'pdf', 'PDF', 'xml', 'XML', 'xls', 'XLS', 'xlsx', 'XLSX']

class SourceModel(QStandardItemModel):
    class Roles(Enum):
        NAME = Qt.UserRole + 1
        TYPE = Qt.UserRole + 2
        PATH = Qt.UserRole + 3
        DATASET_NAME = Qt.UserRole + 5

        def __int__(self):
            return self.value

    def __init__(self):
        super().__init__()

    def data(self, index , role):
        item = self.item(index.row())
        if role == Qt.DisplayRole:
            if item.data(int(SourceModel.Roles.TYPE)) != 'model':
                return self.tr('{} ({})').format(item.data(int(SourceModel.Roles.NAME)), item.data(int(SourceModel.Roles.PATH)))
        if role == Qt.DecorationRole:
            return QIcon(os.path.join(os.path.dirname(__file__), f'../images/file_types/{item.data(int(SourceModel.Roles.TYPE))}.png'))
        return item.data(int(role))

    def add_source(self, name, type, path):
        item = QStandardItem()
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        self.appendRow(item)

    def remove_sources(self, indices):
        for index in sorted(indices):
            self.removeRow(index.row()) 

class ImportModelsModel(SourceModel):

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
        self._checked_models = {}
        
    
    def refresh_model(self, filtered_source_model, db_connector=None):

        self.clear()
        previously_checked_models = self._checked_models
        self._checked_models = {}

        # models from db
        db_modelnames = self.db_modelnames(db_connector)
        print( f'db_modelnames {db_modelnames}')

        # models from the repos
        models_from_repo =[]
        filtered_source_model.setFilterFixedString('model')
        for r in range(0,filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r,0)
            modelname = filtered_source_model_index.data(int(SourceModel.Roles.NAME))
            if modelname and modelname not in ImportModelsModel.blacklist and modelname not in db_modelnames:
                self.add_source(modelname, filtered_source_model_index.data(int(SourceModel.Roles.TYPE)), filtered_source_model_index.data(int(SourceModel.Roles.PATH)), previously_checked_models.get(modelname, Qt.Checked))
                models_from_repo.append(filtered_source_model_index.data(int(SourceModel.Roles.NAME)))
            else:
                print(f"repo filtered modelname {modelname}")
        print( f'models_from_repo {models_from_repo}')

        # models from the files
        models_from_ili_files=[]
        filtered_source_model.setFilterFixedString('ili')
        for r in range(0,filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r,0)
            ili_file_path = filtered_source_model_index.data(int(SourceModel.Roles.PATH))
            self.ilicache = IliCache(None, ili_file_path)
            models = self.ilicache.process_ili_file(ili_file_path)
            for model in models:
                if model['name'] and model['name'] not in ImportModelsModel.blacklist and model['name'] not in db_modelnames:
                    self.add_source(model['name'], filtered_source_model_index.data(int(SourceModel.Roles.TYPE)), filtered_source_model_index.data(int(SourceModel.Roles.PATH)), previously_checked_models.get(model['name'], Qt.Checked if model is models[-1] else Qt.Unchecked))
                    models_from_ili_files.append(model['name'])
                else:
                    print(f"ilifile filtered modelname {model['name']}")
        print( f'models_from_ili_files {models_from_ili_files}')

        # models from the transfer files
        # dave not yet integrated...
        # models_from_transfer_files=[]
        # filtered_source_model.setFilterRegExp('|'.join(TransferExtensions))
        # for r in range(0,filtered_source_model.rowCount()):
        #    index = filtered_source_model.index(r,0)
        #    ili_file_path = index.data(int(SourceModel.Roles.PATH))
        #    models_from_transfer_files.append(ili_file_path)
        # print( f'models_from_transfer_files {models_from_transfer_files}')

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

    def db_modelnames(self, db_connector=None):
        modelnames = list()
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r'(?:\{[^\}]*\}|\s)')
                    for modelname in regex.split(db_model['modelname']):
                        modelnames.append(modelname.strip())
        return modelnames

    def add_source(self, name, type, path, checked):

        item = QStandardItem()
        self._checked_models[name] = checked
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        self.appendRow(item)

        # problem, maybe later
        # super().add_source(name, type, path, item

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            if self.data(index, int(SourceModel.Roles.NAME)) in self._checked_models:
                return self._checked_models[self.data(index, int(SourceModel.Roles.NAME))]
            else:
                print(f"{self.data(index, int(SourceModel.Roles.NAME))} is not in checked models1")
        else:
            return SourceModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            if self.data(index, int(SourceModel.Roles.NAME)) in self._checked_models:
                self._checked_models[self.data(index, int(SourceModel.Roles.NAME))] = data
            else:
                print(f"{self.data(index, int(SourceModel.Roles.NAME))} is not in checked models2")

    def check(self, index):
        if self.data(index, Qt.CheckStateRole) == Qt.Checked:
            self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
        else:
            self.setData(index, Qt.CheckStateRole, Qt.Checked)

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
        self.file_model.setFilterRole(int(SourceModel.Roles.TYPE))

        self.refreshTimer = QTimer()
        self.refreshTimer.setSingleShot(True)
        self.refreshTimer.timeout.connect(self.refresh_import_models_model)

        self.import_models_model = ImportModelsModel()
        self.source_model.rowsInserted.connect( lambda: self.request_for_refresh_import_models_model())
        self.source_model.rowsRemoved.connect( lambda: self.request_for_refresh_import_models_model())

        self.setPage(self.Page_Intro, IntroPage(self))
        self.setPage(self.Page_ImportSourceSeletion, ImportSourceSeletionPage(base_config, self))
        self.setPage(self.Page_ImportDatabaseSelection, ImportDatabaseSelectionPage(base_config, self))
        self.setPage(self.Page_ImportSchemaConfiguration, ImportSchemaConfigurationPage(base_config, self))
        #self.setPage(self.Page_ImportDataConfigurtation, ImportDataConfigurtationPage())

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"));
        self.setWizardStyle(QWizard.ModernStyle);

    def request_for_refresh_import_models_model(self):
        # hold refresh back
        self.refreshTimer.start(500)

    def refresh_import_models_model(self):
        self.import_models_model.refresh_model(self.file_model, None) 
