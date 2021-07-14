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

from QgisModelBaker.utils.qt_utils import make_folder_selector
from enum import Enum
import os
import re

from qgis.PyQt.QtWidgets import (
    QWizard,
    QTextBrowser,
    QSizePolicy,
    QGridLayout
)

from QgisModelBaker.gui.intro_page import IntroPage
from QgisModelBaker.gui.import_source_selection_page import ImportSourceSeletionPage
from QgisModelBaker.gui.import_database_selection_page import ImportDatabaseSelectionPage
from QgisModelBaker.gui.import_schema_configuration_page import ImportSchemaConfigurationPage
from QgisModelBaker.gui.import_execution_page import ImportExecutionPage

from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QIcon
)

from qgis.gui import (
    QgsMessageBar
)

from qgis.PyQt.QtCore import (
    QSortFilterProxyModel,
    QTimer,
    Qt
)

from QgisModelBaker.libili2db.ilicache import IliCache
from QgisModelBaker.libili2db.ili2dbconfig import ImportDataConfiguration, SchemaImportConfiguration

from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError

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

        # this would lead to problem, maybe later
        # SourceModel.add_source(name, type, path, item

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role):
        if role == Qt.CheckStateRole:
            return self._checked_models[self.data(index, int(SourceModel.Roles.NAME))]
        else:
            return SourceModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self.beginResetModel()
            self._checked_models[self.data(index, int(SourceModel.Roles.NAME))] = data
            self.endResetModel()

    def check(self, index):
        if self.data(index, Qt.CheckStateRole) == Qt.Checked:
            self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
        else:
            self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def import_sessions(self):
        sessions = {}
        for r in range(0,self.rowCount()):
            index = self.index(r,0)
            if index.data(int(Qt.Checked)):
                type = index.data(int(SourceModel.Roles.TYPE))
                source = index.data(int(SourceModel.Roles.PATH)) if type != 'model' else 'repository'
                model = index.data(int(SourceModel.Roles.NAME))
                
                if self._checked_models[model] == Qt.Checked:
                    models = []
                    if source in sessions:
                        models = sessions[source]['models']
                    else:
                        sessions[source]={}
                    models.append(model)
                    sessions[source]['models']=models
        return sessions

    def checked_models(self):
        return [model for model in self._checked_models.keys() if self._checked_models[model] == Qt.Checked]

class ImportWizard (QWizard):

    Page_Intro_Id = 1
    Page_ImportSourceSeletion_Id = 2
    Page_ImportDatabaseSelection_Id = 3
    Page_ImportSchemaConfiguration_Id = 4
    Page_ImportExecution_Id = 5
    Page_ImportDataConfigurtation_Id = 6

    def __init__(self, base_config, parent=None):
        QWizard.__init__(self)

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"));
        self.setWizardStyle(QWizard.ModernStyle);

        self.current_id = 0

        # config setup
        self.configuration = SchemaImportConfiguration()
        self.configuration.base_configuration = base_config

        # models setup
        self.db_simple_factory = DbSimpleFactory()

        self.source_model = SourceModel()
        self.file_model = QSortFilterProxyModel()
        self.file_model.setSourceModel(self.source_model)
        self.file_model.setFilterRole(int(SourceModel.Roles.TYPE))
        self.import_models_model = ImportModelsModel()

        # pages setup
        self.intro_page = IntroPage(self)
        self.source_seletion_page = ImportSourceSeletionPage(self)
        self.database_seletion_page = ImportDatabaseSelectionPage(self)
        self.schema_configuration_page = ImportSchemaConfigurationPage(self)
        self.execution_page = ImportExecutionPage(self)
        
        self.setPage(self.Page_Intro_Id, self.intro_page)
        self.setPage(self.Page_ImportSourceSeletion_Id, self.source_seletion_page)
        self.setPage(self.Page_ImportDatabaseSelection_Id, self.database_seletion_page)
        self.setPage(self.Page_ImportSchemaConfiguration_Id, self.schema_configuration_page)
        self.setPage(self.Page_ImportExecution_Id, self.execution_page)
        #self.setPage(self.Page_ImportDataConfigurtation_Id, ImportDataConfigurtationPage())

        self.currentIdChanged.connect(self.id_changed)
    
    def id_changed(self, new_id):
        if self.current_id == self.Page_ImportDatabaseSelection_Id:
            self.database_seletion_page.save_configuration(self.configuration)
        if self.current_id == self.Page_ImportSchemaConfiguration_Id:
            self.schema_configuration_page.save_configuration(self.configuration)

        self.current_id = new_id

        if self.current_id == self.Page_ImportDatabaseSelection_Id:
            self.database_seletion_page.restore_configuration(self.configuration)
        if self.current_id == self.Page_ImportSchemaConfiguration_Id:
            self.refresh_import_models_model()
            self.schema_configuration_page.restore_configuration(self.configuration)
        if self.current_id == self.Page_ImportExecution_Id:
            self.execution_page.run(self.configuration, self.import_models_model.import_sessions())

    def refresh_import_models_model(self):

        schema = self.configuration.dbschema
        db_factory = self.db_simple_factory.create_factory(self.configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(self.configuration)
        uri_string = config_manager.get_uri(self.configuration.db_use_super_login)
        db_connector = None
        try:
            db_connector = db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            # when wrong connection parameters entered, there should just be returned an empty model - so let it pass
            pass

        self.import_models_model.refresh_model(self.file_model, db_connector) 
