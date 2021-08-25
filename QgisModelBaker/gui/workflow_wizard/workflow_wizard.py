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

from qgis.PyQt.QtCore import (
    QSortFilterProxyModel,
    QTimer,
    Qt,
    QEventLoop,
    pyqtSignal,
    QStringListModel
)

from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QIcon
)

from qgis.PyQt.QtWidgets import (
    QWizard,
    QDialog,
    QVBoxLayout
)

from qgis.gui import (
    QgsMessageBar
)

from QgisModelBaker.gui.workflow_wizard.intro_page import IntroPage
from QgisModelBaker.gui.workflow_wizard.import_source_selection_page import ImportSourceSeletionPage
from QgisModelBaker.gui.workflow_wizard.database_selection_page import DatabaseSelectionPage
from QgisModelBaker.gui.workflow_wizard.import_schema_configuration_page import ImportSchemaConfigurationPage
from QgisModelBaker.gui.workflow_wizard.execution_page import ExecutionPage
from QgisModelBaker.gui.workflow_wizard.project_creation_page import ProjectCreationPage
from QgisModelBaker.gui.workflow_wizard.import_data_configuration_page import ImportDataConfigurationPage
from QgisModelBaker.gui.workflow_wizard.export_data_configuration_page import ExportDataConfigurationPage
from QgisModelBaker.gui.workflow_wizard.import_data_configuration_page import SourceModel
from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType

from QgisModelBaker.libili2db.ilicache import (
    IliCache,
    IliToppingFileCache
)

from QgisModelBaker.libili2db.ili2dbconfig import (
    UpdateDataConfiguration,
    SchemaImportConfiguration,
    ExportConfiguration
)

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError

IliExtensions = ['ili']
TransferExtensions = ['xtf', 'XTF', 'itf', 'ITF', 'pdf',
                      'PDF', 'xml', 'XML', 'xls', 'XLS', 'xlsx', 'XLSX']
class ImportModelsModel(SourceModel):

    def __init__(self):
        super().__init__()
        self._checked_models = {}

    def refresh_model(self, filtered_source_model, db_connector=None, silent=False):

        self.clear()
        previously_checked_models = self._checked_models
        self._checked_models = {}

        # models from db
        db_modelnames = self.db_modelnames(db_connector)

        # models from the repos
        models_from_repo = []
        filtered_source_model.setFilterFixedString('model')
        for r in range(0, filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r, 0)
            modelname = filtered_source_model_index.data(
                int(SourceModel.Roles.NAME))
            if modelname:
                enabled = modelname not in db_modelnames
                self.add_source(modelname, filtered_source_model_index.data(int(SourceModel.Roles.TYPE)), filtered_source_model_index.data(
                    int(SourceModel.Roles.PATH)), previously_checked_models.get(modelname, Qt.Checked) if enabled else Qt.Unchecked, enabled)
                models_from_repo.append(
                    filtered_source_model_index.data(int(SourceModel.Roles.NAME)))
                if not silent:
                    self.print_info.emit(
                        self.tr("- Append (repository) model {}{}").format(modelname, " (inactive because it already exists in the database)" if not enabled else ''))

        # models from the files
        models_from_ili_files = []
        filtered_source_model.setFilterFixedString('ili')
        for r in range(0, filtered_source_model.rowCount()):
            filtered_source_model_index = filtered_source_model.index(r, 0)
            ili_file_path = filtered_source_model_index.data(
                int(SourceModel.Roles.PATH))
            self.ilicache = IliCache(None, ili_file_path)
            models = self.ilicache.process_ili_file(ili_file_path)
            for model in models:
                if model['name']:
                    enabled = model['name'] not in db_modelnames
                    self.add_source(model['name'], filtered_source_model_index.data(int(SourceModel.Roles.TYPE)), filtered_source_model_index.data(
                        int(SourceModel.Roles.PATH)), previously_checked_models.get(model['name'], Qt.Checked if model is models[-1] and enabled else Qt.Unchecked), enabled)
                    models_from_ili_files.append(model['name'])
                    if not silent:
                        self.print_info.emit(
                            self.tr("- Append (file) model {}{} from {}").format(model['name'], " (inactive because it already exists in the database)" if not enabled else '', ili_file_path))

        # models from the transfer files (not yet implemented)
        filtered_source_model.setFilterRegExp('|'.join(TransferExtensions))
        for r in range(0, filtered_source_model.rowCount()):
            index = filtered_source_model.index(r, 0)
            xtf_file_path = index.data(int(SourceModel.Roles.PATH))
            if not silent:
                self.print_info.emit(
                    self.tr("Get models from the transfer file ({}) is not yet implemented").format(xtf_file_path))

        return self.rowCount()

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

    def add_source(self, name, type, path, checked, enabled):
        item = QStandardItem()
        self._checked_models[name] = checked
        item.setFlags(Qt.ItemIsSelectable |
                      Qt.ItemIsEnabled if enabled else Qt.NoItemFlags)
        item.setData(name, int(Qt.DisplayRole))
        item.setData(name, int(SourceModel.Roles.NAME))
        item.setData(type, int(SourceModel.Roles.TYPE))
        item.setData(path, int(SourceModel.Roles.PATH))
        self.appendRow(item)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.tr("{}{}").format(SourceModel.data(self, index, (Qt.DisplayRole)), "" if index.flags() & Qt.ItemIsEnabled else " (already in the database)")
        if role == Qt.CheckStateRole:
            return self._checked_models[self.data(index, int(SourceModel.Roles.NAME))]
        return SourceModel.data(self, index, role)

    def setData(self, index, role, data):
        if role == Qt.CheckStateRole:
            self.beginResetModel()
            self._checked_models[self.data(
                index, int(SourceModel.Roles.NAME))] = data
            self.endResetModel()

    def flags(self, index):
        item = self.item(index.row(), index.column())
        if item:
            return item.flags()
        return Qt.NoItemFlags

    def check(self, index):
        if index.flags() & Qt.ItemIsEnabled:
            if self.data(index, Qt.CheckStateRole) == Qt.Checked:
                self.setData(index, Qt.CheckStateRole, Qt.Unchecked)
            else:
                self.setData(index, Qt.CheckStateRole, Qt.Checked)

    def import_sessions(self):
        sessions = {}
        for r in range(0, self.rowCount()):
            item = self.index(r, 0)
            if item.data(int(Qt.Checked)):
                type = item.data(int(SourceModel.Roles.TYPE))
                model = item.data(int(SourceModel.Roles.NAME))
                source = item.data(int(SourceModel.Roles.PATH)
                                   ) if type != 'model' else 'repository '+model

                if self._checked_models[model] == Qt.Checked:
                    models = []
                    if source in sessions:
                        models = sessions[source]['models']
                    else:
                        sessions[source] = {}
                    models.append(model)
                    sessions[source]['models'] = models
        return sessions

    def checked_models(self):
        return [model for model in self._checked_models.keys() if self._checked_models[model] == Qt.Checked]

class ImportDataModel(QSortFilterProxyModel):

    print_info = pyqtSignal([str], [str, str])

    def __init__(self):
        super().__init__()
        self._checked_models = {}

    def import_sessions(self, order_list):
        sessions = {}
        i = 0
        for r in order_list:
            source = self.index(r, 0).data(int(SourceModel.Roles.PATH))
            dataset = self.index(r, 1).data(
                int(SourceModel.Roles.DATASET_NAME))
            sessions[source] = {}
            sessions[source]['dataset'] = dataset
            i += 1
        return sessions
        
class ExportModelsModel(QStringListModel):
    # at dave: can we find synergies here with the dataset model of the dataset manager
    # dann wärs ein standarditemmodel - das handling der checked_models (bzw. checked_datasets wär dann wie im ImportModelsModel)
    # evtl. könnte man es dann auch gleich fürs ExportModelsModel machen
    # oder zumindest ExportDatasetsModel und ExportModelsModel

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

    def refresh_model(self, db_connector=None):
        modelnames = []
        
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                for db_model in db_models:
                    regex = re.compile(r'(?:\{[^\}]*\}|\s)')
                    for modelname in regex.split(db_model['modelname']):
                        if modelname and modelname not in ExportModelsModel.blacklist:
                            modelnames.append(modelname.strip())

        self.setStringList(modelnames)

        self._checked_models = {modelname: Qt.Checked for modelname in modelnames}

        return self.rowCount()

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
    
    def check_all(self):
        for name in self.stringList():
            self._checked_models[name] = Qt.Checked

    def checked_models(self):
        return [modelname for modelname in self.stringList() if self._checked_models[modelname] == Qt.Checked]

        self.editor = QComboBox(parent)
        self.editor.addItems(self.items)
class ExportDatasetsModel(QStringListModel):
    def __init__(self):
        super().__init__()
        self._selected_dataset = None

    def refresh_model(self, db_connector=None):
        datasetnames = []
        
        if db_connector and db_connector.db_or_schema_exists():
            datasets_info = db_connector.get_datasets_info()
            for record in datasets_info:
                datasetnames.append(record['datasetname'])
        self.setStringList(datasetnames)
        if datasetnames:
            self._selected_dataset = datasetnames[0]
        return self.rowCount()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def select(self, row):
        self._selected_dataset = self.data(self.index(row,0), Qt.DisplayRole)
    
    def selected_dataset(self):
        return self._selected_dataset

class WorkflowWizard (QWizard):

    Page_Intro_Id = 1
    Page_ImportSourceSeletion_Id = 2
    Page_ImportDatabaseSelection_Id = 3
    Page_GenerateDatabaseSelection_Id = 4
    Page_ImportSchemaConfiguration_Id = 5
    Page_ImportSchemaExecution_Id = 6
    Page_ImportDataConfiguration_Id = 7
    Page_ImportDataExecution_Id = 8
    Page_ExportDatabaseSelection_Id = 9
    Page_ExportDataConfiguration_Id = 10
    Page_ExportDataExecution_Id = 11
    Page_ProjectCreation_Id = 12

    def __init__(self, iface, base_config, parent):
        QWizard.__init__(self)

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"))
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoCancelButtonOnLastPage)

        self.current_id = 0

        self.iface = iface
        self.log_panel = parent.log_panel

        # config setup
        self.db_simple_factory = DbSimpleFactory()
        self.import_schema_configuration = SchemaImportConfiguration()
        self.import_data_configuration = UpdateDataConfiguration()
        self.export_data_configuration = ExportConfiguration()
        self.import_schema_configuration.base_configuration = base_config
        self.import_data_configuration.base_configuration = base_config
        self.export_data_configuration.base_configuration = base_config

        # models setup
        self.source_model = SourceModel()
        self.source_model.print_info.connect(self.log_panel.print_info)

        self.file_model = QSortFilterProxyModel()
        self.file_model.setSourceModel(self.source_model)
        self.file_model.setFilterRole(int(SourceModel.Roles.TYPE))
        self.import_models_model = ImportModelsModel()
        self.import_models_model.print_info.connect(self.log_panel.print_info)

        self.import_data_file_model = ImportDataModel()
        self.import_data_file_model.print_info.connect(
            self.log_panel.print_info)
        self.import_data_file_model.setSourceModel(self.source_model)
        self.import_data_file_model.setFilterRole(int(SourceModel.Roles.TYPE))
        self.import_data_file_model.setFilterRegExp(
            '|'.join(TransferExtensions))
        
        self.export_models_model = ExportModelsModel()
        self.export_datasets_model = ExportDatasetsModel()
        self.current_export_target = ""
        # dave oder sollen wir current_export_target aus dem export_data_configuration_page holen?

        # pages setup
        self.intro_page = IntroPage(
            self, self._current_page_title(self.Page_Intro_Id))

        # import
        self.source_seletion_page = ImportSourceSeletionPage(
            self, self._current_page_title(self.Page_ImportSourceSeletion_Id))
        self.import_database_seletion_page = DatabaseSelectionPage(
            self, self._current_page_title(self.Page_ImportDatabaseSelection_Id), DbActionType.IMPORT_DATA)
        self.schema_configuration_page = ImportSchemaConfigurationPage(
            self, self._current_page_title(self.Page_ImportSchemaConfiguration_Id))
        self.import_schema_execution_page = ExecutionPage(
            self, self._current_page_title(self.Page_ImportSchemaExecution_Id), DbActionType.GENERATE)
        self.data_configuration_page = ImportDataConfigurationPage(
            self, self._current_page_title(self.Page_ImportDataConfiguration_Id))
        self.import_data_execution_page = ExecutionPage(
            self, self._current_page_title(self.Page_ImportDataExecution_Id), DbActionType.IMPORT_DATA)
        self.project_creation_page = ProjectCreationPage(
            self, self._current_page_title(self.Page_ProjectCreation_Id))

        self.setPage(self.Page_Intro_Id, self.intro_page)
        self.setPage(self.Page_ImportSourceSeletion_Id,
                     self.source_seletion_page)
        self.setPage(self.Page_ImportDatabaseSelection_Id,
                     self.import_database_seletion_page)
        self.setPage(self.Page_ImportSchemaConfiguration_Id,
                     self.schema_configuration_page)
        self.setPage(self.Page_ImportSchemaExecution_Id, self.import_schema_execution_page)
        self.setPage(self.Page_ImportDataConfiguration_Id,
                     self.data_configuration_page)
        self.setPage(self.Page_ImportDataExecution_Id,
                     self.import_data_execution_page)
        self.setPage(self.Page_ProjectCreation_Id,
                     self.project_creation_page)

        # bake project
        self.generate_database_seletion_page = DatabaseSelectionPage(
            self, self._current_page_title(self.Page_GenerateDatabaseSelection_Id), DbActionType.GENERATE)
        self.setPage(self.Page_GenerateDatabaseSelection_Id,
                     self.generate_database_seletion_page)

        # export not yet implemented
        self.export_database_seletion_page = DatabaseSelectionPage(self, self._current_page_title(self.Page_ExportDatabaseSelection_Id), DbActionType.EXPORT)
        self.export_data_configuration_page = ExportDataConfigurationPage(self, self._current_page_title(self.Page_ExportDataConfiguration_Id))
        self.export_data_execution_page = ExecutionPage(self, self._current_page_title(self.Page_ExportDataExecution_Id), DbActionType.EXPORT)
        self.setPage(self.Page_ExportDatabaseSelection_Id,
                     self.export_database_seletion_page)
        self.setPage(self.Page_ExportDataConfiguration_Id,
                     self.export_data_configuration_page)
        self.setPage(self.Page_ExportDataExecution_Id,
                     self.export_data_execution_page)

        self.currentIdChanged.connect(self.id_changed)

    def next_id(self):
        # this is called on the nextId overrides of the pages - so after the next-button is pressed
        # it finalizes the edits on the current page and returns the evaluated id of the next page
        if self.current_id == self.Page_ImportSourceSeletion_Id:
            return self.Page_ImportDatabaseSelection_Id

        if self.current_id == self.Page_ImportDatabaseSelection_Id:
            # update configuration for import data and for import schema and use schema config to save
            self.import_database_seletion_page.update_configuration(
                self.import_schema_configuration)
            self.import_database_seletion_page.update_configuration(
                self.import_data_configuration)
            self.import_database_seletion_page.save_configuration(
                self.import_schema_configuration)
            if self.refresh_import_models(True):
                return self.Page_ImportSchemaConfiguration_Id
            if self.import_data_file_model.rowCount():
                return self.Page_ImportDataConfiguration_Id
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_GenerateDatabaseSelection_Id:
            # update configuration for project generation for import schema and use schema config to save
            self.generate_database_seletion_page.update_configuration(
                self.import_schema_configuration)
            self.generate_database_seletion_page.update_configuration(
                self.import_data_configuration)
            self.generate_database_seletion_page.save_configuration(
                self.import_schema_configuration)
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_ImportSchemaConfiguration_Id:
            self.schema_configuration_page.update_configuration(
                self.import_schema_configuration)
            self.schema_configuration_page.save_configuration(
                self.import_schema_configuration)
            if len(self.import_models_model.checked_models()):
                return self.Page_ImportSchemaExecution_Id
            if self.import_data_file_model.rowCount():
                return self.Page_ImportDataConfiguration_Id
            #dave else close

        if self.current_id == self.Page_ImportSchemaExecution_Id:
            if self.import_data_file_model.rowCount():
                return self.Page_ImportDataConfiguration_Id
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_ImportDataConfiguration_Id:
            return self.Page_ImportDataExecution_Id

        if self.current_id == self.Page_ImportDataExecution_Id:
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_ExportDatabaseSelection_Id:
            # update configuration for import data and for import schema and use schema config to save
            self.export_database_seletion_page.update_configuration(
                self.export_data_configuration)
            self.export_database_seletion_page.save_configuration(
                self.export_data_configuration)
            return self.Page_ExportDataConfiguration_Id
        
        if self.current_id == self.Page_ExportDataConfiguration_Id:
            return self.Page_ExportDataExecution_Id
        
        # fallback
        return(self.current_id)

    def id_changed(self, new_id):
        self.current_id = new_id

        self.log_panel.print_info(
            self.tr(f" > ---------- {self._current_page_title(self.current_id)}"))

        if self.current_id == self.Page_ImportDatabaseSelection_Id:
            # use schema config to restore
            self.import_database_seletion_page.restore_configuration(
                self.import_schema_configuration)

        if self.current_id == self.Page_GenerateDatabaseSelection_Id:
            self.generate_database_seletion_page.restore_configuration(
                self.import_schema_configuration)

        if self.current_id == self.Page_ExportDatabaseSelection_Id:
            self.export_database_seletion_page.restore_configuration(
                self.export_data_configuration)

        if self.current_id == self.Page_ImportSchemaConfiguration_Id:
            self.refresh_import_models()
            self.schema_configuration_page.restore_configuration()

        if self.current_id == self.Page_ImportSchemaExecution_Id:
            self.import_schema_execution_page.setup_sessions(
                self.import_schema_configuration, self.import_models_model.import_sessions())

        if self.current_id == self.Page_ProjectCreation_Id:
            self.project_creation_page.set_configuration(
                self.import_schema_configuration)

        if self.current_id == self.Page_ImportDataConfiguration_Id:
            self.data_configuration_page.setup_dialog()

        if self.current_id == self.Page_ImportDataExecution_Id:
            self.import_data_execution_page.setup_sessions(self.import_data_configuration, self.import_data_file_model.import_sessions(
                self.data_configuration_page.order_list()))
        
        if self.current_id == self.Page_ExportDataConfiguration_Id:
            self.refresh_export_models()
        
        if self.current_id == self.Page_ExportDataExecution_Id:
            sessions = {}
            sessions[self.current_export_target] = {}
            sessions[self.current_export_target]['models']=self.export_models_model.checked_models()
            sessions[self.current_export_target]['dataset']=self.export_datasets_model.selected_dataset()
            self.export_data_execution_page.setup_sessions(self.export_data_configuration, sessions)           

    def refresh_import_models(self, silent=False):
        db_connector=self._get_db_connector(self.import_schema_configuration, self.db_simple_factory)
        return self.import_models_model.refresh_model(self.file_model, db_connector, silent)

    def refresh_export_models(self):
        db_connector=self._get_db_connector(self.export_data_configuration, self.db_simple_factory)
        self.export_models_model.refresh_model(db_connector)
        self.export_datasets_model.refresh_model(db_connector)
        return 

    def get_topping_file_list(self, id_list, log_panel):
        topping_file_model = self.get_topping_file_model(id_list, log_panel)
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1)
            if matches:
                file_path = matches[0].data(
                    int(topping_file_model.Roles.LOCALFILEPATH))
                log_panel.print_info(
                    self.tr('- - Got file {}').format(file_path), LogPanel.COLOR_TOPPING)
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, id_list, log_panel):
        topping_file_cache = IliToppingFileCache(
            self.import_schema_configuration.base_configuration, id_list)

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()
        log_panel.print_info(self.tr('- - Downloading…'),
                             LogPanel.COLOR_TOPPING)

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        if len(topping_file_cache.downloaded_files) == len(id_list):
            log_panel.print_info(self.tr(
                '- - All topping files successfully downloaded'), LogPanel.COLOR_TOPPING)
        else:
            missing_file_ids = id_list
            for downloaded_file_id in topping_file_cache.downloaded_files:
                if downloaded_file_id in missing_file_ids:
                    missing_file_ids.remove(downloaded_file_id)
            log_panel.print_info(self.tr('- - Some topping files where not successfully downloaded: {}').format(
                ' '.join(missing_file_ids)), LogPanel.COLOR_TOPPING)

        return topping_file_cache.model

    def _current_page_title(self, id):
        if id == self.Page_ImportSourceSeletion_Id:
            return self.tr("Source Selection")
        elif id == self.Page_ImportDatabaseSelection_Id:
            return self.tr("Database Configuration")
        elif id == self.Page_GenerateDatabaseSelection_Id:
            return self.tr("Database Configuration")
        elif id == self.Page_ImportSchemaConfiguration_Id:
            return self.tr("Schema Import Configuration")
        elif id == self.Page_ImportSchemaExecution_Id:
            return self.tr("Schema Import Sessions")
        elif id == self.Page_ImportDataConfiguration_Id:
            return self.tr("Data import configuration")
        elif id == self.Page_ImportDataExecution_Id:
            return self.tr("Data Import Sessions")
        elif id == self.Page_ExportDataConfiguration_Id:
            return self.tr("Data export configuration")
        elif id == self.Page_ExportDataExecution_Id:
            return self.tr("Data export Sessions")
        elif id == self.Page_ProjectCreation_Id:
            return self.tr("Generate a QGIS Project")
        else:
            return self.tr("Model Baker - Workflow Wizard")

    def _get_db_connector(self, configuration, db_simple_factory):
        # migth be moved to db_utils...
        schema = configuration.dbschema

        db_factory = db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        try:
            return db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            return None

class WorkflowWizardDialog (QDialog):

    def __init__(self, iface, base_config, parent=None):
        QDialog.__init__(self)
        self.iface = iface
        self.base_config = base_config

        self.setWindowTitle(self.tr("QGIS Model Baker - Workflow Wizard"))
        self.log_panel = LogPanel()
        self.workflow_wizard = WorkflowWizard(
            self.iface, self.base_config, self)
        self.workflow_wizard.setStartId(self.workflow_wizard.Page_Intro_Id)
        self.workflow_wizard.setWindowFlags(Qt.Widget)
        self.workflow_wizard.show()

        self.workflow_wizard.finished.connect(self.done)
        layout = QVBoxLayout()
        layout.addWidget(self.workflow_wizard)
        layout.addWidget(self.log_panel)
        self.setLayout(layout)
