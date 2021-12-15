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
import os
import pathlib
import re

from qgis.PyQt.QtCore import QEventLoop, Qt, QTimer
from qgis.PyQt.QtWidgets import QDialog, QSplitter, QVBoxLayout, QWizard

import QgisModelBaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.log_panel import LogPanel
from QgisModelBaker.gui.workflow_wizard.database_selection_page import (
    DatabaseSelectionPage,
)
from QgisModelBaker.gui.workflow_wizard.execution_page import ExecutionPage
from QgisModelBaker.gui.workflow_wizard.export_data_configuration_page import (
    ExportDataConfigurationPage,
)
from QgisModelBaker.gui.workflow_wizard.import_data_configuration_page import (
    ImportDataConfigurationPage,
)
from QgisModelBaker.gui.workflow_wizard.import_schema_configuration_page import (
    ImportSchemaConfigurationPage,
)
from QgisModelBaker.gui.workflow_wizard.import_source_selection_page import (
    ImportSourceSelectionPage,
)
from QgisModelBaker.gui.workflow_wizard.intro_page import IntroPage
from QgisModelBaker.gui.workflow_wizard.project_creation_page import ProjectCreationPage
from QgisModelBaker.libili2db.globals import DbActionType
from QgisModelBaker.libili2db.ili2dbconfig import (
    ExportConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
    UpdateDataConfiguration,
)
from QgisModelBaker.libili2db.ilicache import IliDataCache, IliToppingFileCache
from QgisModelBaker.utils.gui_utils import (
    ImportDataModel,
    ImportModelsModel,
    PageIds,
    SchemaBasketsModel,
    SchemaDataFilterMode,
    SchemaDatasetsModel,
    SchemaModelsModel,
    SourceModel,
    TransferExtensions,
)

from ...utils.gui_utils import LogColor


class WorkflowWizard(QWizard):
    def __init__(self, iface, base_config, parent):
        QWizard.__init__(self, parent)

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"))
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoCancelButtonOnLastPage)

        self.current_id = 0

        self.iface = iface
        self.log_panel = parent.log_panel

        # configuration objects are keeped on top level to be able to access them from individual pages
        self.base_config = base_config
        self.import_schema_configuration = SchemaImportConfiguration()
        self.import_data_configuration = ImportDataConfiguration()
        self.update_data_configuration = UpdateDataConfiguration()
        self.export_data_configuration = ExportConfiguration()
        self.import_schema_configuration.base_configuration = self.base_config
        self.import_data_configuration.base_configuration = self.base_config
        self.update_data_configuration.base_configuration = self.base_config
        self.export_data_configuration.base_configuration = self.base_config

        # data models are keeped on top level because sometimes they need to be accessed to evaluate the wizard workflow
        # the source_model keeps all the sources (files or repositories) used and the dataset property
        self.source_model = SourceModel()
        self.source_model.print_info.connect(self.log_panel.print_info)

        # the import_models_model keeps every single model as entry and a checked state
        self.import_models_model = ImportModelsModel()
        self.import_models_model.print_info.connect(self.log_panel.print_info)

        # the import_data_file_model keeps the filtered out transfer files (from source model) and functions to get ordered import sessions
        self.import_data_file_model = ImportDataModel()
        self.import_data_file_model.print_info.connect(self.log_panel.print_info)
        self.import_data_file_model.setSourceModel(self.source_model)
        self.import_data_file_model.setFilterRole(int(SourceModel.Roles.TYPE))
        self.import_data_file_model.setFilterRegExp("|".join(TransferExtensions))
        self.ilireferencedatacache = IliDataCache(
            self.import_schema_configuration.base_configuration,
            "referenceData",
        )
        self.ilireferencedatacache.new_message.connect(self.log_panel.show_message)

        # the export_models_model keeps every single model found in the current database and keeps the selected models
        self.export_models_model = SchemaModelsModel()
        # the export_datasets_model keeps every dataset found in the current database and keeps the selected dataset
        self.export_datasets_model = SchemaDatasetsModel()
        # the export_baskets_model keeps every baskets found in the current database and keeps the selected baskets
        self.export_baskets_model = SchemaBasketsModel()

        # the current export target is the current set target file for the export. It's keeped top level to have a consequent behavior of those information.
        self.current_export_target = ""
        self.current_export_filter = SchemaDataFilterMode.NO_FILTER

        # pages setup
        self.intro_page = IntroPage(self, self._current_page_title(PageIds.Intro))
        self.source_selection_page = ImportSourceSelectionPage(
            self, self._current_page_title(PageIds.ImportSourceSelection)
        )
        self.import_database_selection_page = DatabaseSelectionPage(
            self,
            self._current_page_title(PageIds.ImportDatabaseSelection),
            DbActionType.IMPORT_DATA,
        )
        self.schema_configuration_page = ImportSchemaConfigurationPage(
            self, self._current_page_title(PageIds.ImportSchemaConfiguration)
        )
        self.import_schema_execution_page = ExecutionPage(
            self,
            self._current_page_title(PageIds.ImportSchemaExecution),
            DbActionType.GENERATE,
        )
        self.data_configuration_page = ImportDataConfigurationPage(
            self, self._current_page_title(PageIds.ImportDataConfiguration)
        )
        self.import_data_execution_page = ExecutionPage(
            self,
            self._current_page_title(PageIds.ImportDataExecution),
            DbActionType.IMPORT_DATA,
        )
        self.project_creation_page = ProjectCreationPage(
            self, self._current_page_title(PageIds.ProjectCreation)
        )
        self.generate_database_selection_page = DatabaseSelectionPage(
            self,
            self._current_page_title(PageIds.GenerateDatabaseSelection),
            DbActionType.GENERATE,
        )
        self.export_database_selection_page = DatabaseSelectionPage(
            self,
            self._current_page_title(PageIds.ExportDatabaseSelection),
            DbActionType.EXPORT,
        )
        self.export_data_configuration_page = ExportDataConfigurationPage(
            self, self._current_page_title(PageIds.ExportDataConfiguration)
        )
        self.export_data_execution_page = ExecutionPage(
            self,
            self._current_page_title(PageIds.ExportDataExecution),
            DbActionType.EXPORT,
        )
        self.setPage(PageIds.Intro, self.intro_page)
        self.setPage(PageIds.ImportSourceSelection, self.source_selection_page)
        self.setPage(
            PageIds.ImportDatabaseSelection, self.import_database_selection_page
        )
        self.setPage(PageIds.ImportSchemaConfiguration, self.schema_configuration_page)
        self.setPage(PageIds.ImportSchemaExecution, self.import_schema_execution_page)
        self.setPage(PageIds.ImportDataConfiguration, self.data_configuration_page)
        self.setPage(PageIds.ImportDataExecution, self.import_data_execution_page)
        self.setPage(PageIds.ProjectCreation, self.project_creation_page)
        self.setPage(
            PageIds.GenerateDatabaseSelection, self.generate_database_selection_page
        )
        self.setPage(
            PageIds.ExportDatabaseSelection, self.export_database_selection_page
        )
        self.setPage(
            PageIds.ExportDataConfiguration, self.export_data_configuration_page
        )
        self.setPage(PageIds.ExportDataExecution, self.export_data_execution_page)

        self.currentIdChanged.connect(self.id_changed)

    def next_id(self):
        # this is called on the nextId overrides of the pages - so after the next-button is pressed
        # it finalizes the edits on the current page and returns the evaluated id of the next page
        if self.current_id == PageIds.ImportSourceSelection:
            return PageIds.ImportDatabaseSelection

        if self.current_id == PageIds.ImportDatabaseSelection:
            if self.import_database_selection_page.is_valid():
                self._update_configurations(self.import_database_selection_page)
                if self.refresh_import_models(True):
                    # when there are models to import, we go to the configuration page for schema import
                    return PageIds.ImportSchemaConfiguration
                if self.import_data_file_model.rowCount():
                    # when there are transfer files found, we go to the configuration page for data import
                    return PageIds.ImportDataConfiguration
                return PageIds.ProjectCreation

        if self.current_id == PageIds.GenerateDatabaseSelection:
            if self.generate_database_selection_page.is_valid():
                self._update_configurations(self.generate_database_selection_page)
                if self._db_or_schema_exists(self.import_schema_configuration):
                    return PageIds.ProjectCreation
                else:
                    self.log_panel.print_info(
                        self.tr("Database or schema does not exist.")
                    )

        if self.current_id == PageIds.ExportDatabaseSelection:
            if self.export_database_selection_page.is_valid():
                self._update_configurations(self.export_database_selection_page)
                if self._db_or_schema_exists(self.export_data_configuration):
                    self.refresh_export_models()
                    return PageIds.ExportDataConfiguration
                else:
                    self.log_panel.print_info(
                        self.tr("Database or schema does not exist.")
                    )

        if self.current_id == PageIds.ImportSchemaConfiguration:
            self._update_configurations(self.schema_configuration_page)
            if bool(self.import_models_model.checked_models()):
                return PageIds.ImportSchemaExecution
            if (
                self.import_data_file_model.rowCount()
                or self.update_referecedata_cache_model(
                    self._db_modelnames(self.import_data_configuration), "referenceData"
                ).rowCount()
            ):
                return PageIds.ImportDataConfiguration
            else:
                self.log_panel.print_info(
                    self.tr("No models, no transfer files, nothing to do...")
                )

        if self.current_id == PageIds.ImportSchemaExecution:
            # if transfer file available or possible (by getting via UsabILIty Hub)
            if (
                self.import_data_file_model.rowCount()
                or self.update_referecedata_cache_model(
                    self._db_modelnames(self.import_data_configuration), "referenceData"
                ).rowCount()
            ):
                return PageIds.ImportDataConfiguration
            return PageIds.ProjectCreation

        if self.current_id == PageIds.ImportDataConfiguration:
            return PageIds.ImportDataExecution

        if self.current_id == PageIds.ImportDataExecution:
            return PageIds.ProjectCreation

        if self.current_id == PageIds.ExportDataConfiguration:
            return PageIds.ExportDataExecution

        return self.current_id

    def id_changed(self, new_id):
        self.current_id = new_id

        self.log_panel.print_info(
            self.tr(f" > ---------- {self._current_page_title(self.current_id)}")
        )

        if self.current_id == PageIds.ImportDatabaseSelection:
            # use schema config to restore
            self.import_database_selection_page.restore_configuration(
                self.import_schema_configuration
            )

        if self.current_id == PageIds.GenerateDatabaseSelection:
            self.generate_database_selection_page.restore_configuration(
                self.import_schema_configuration
            )

        if self.current_id == PageIds.ExportDatabaseSelection:
            self.export_database_selection_page.restore_configuration(
                self.export_data_configuration
            )

        if self.current_id == PageIds.ImportSchemaConfiguration:
            self.refresh_import_models()
            self.schema_configuration_page.restore_configuration()

        if self.current_id == PageIds.ImportSchemaExecution:
            self.import_schema_execution_page.setup_sessions(
                self.import_schema_configuration,
                self.import_models_model.import_sessions(),
            )

        if self.current_id == PageIds.ProjectCreation:
            self.project_creation_page.set_configuration(
                self.import_schema_configuration
            )

        if self.current_id == PageIds.ImportDataConfiguration:
            self.data_configuration_page.setup_dialog(
                self._basket_handling(self.import_data_configuration)
            )

        if self.current_id == PageIds.ImportDataExecution:
            configuration = (
                self.import_data_configuration
                if not self._basket_handling(self.import_data_configuration)
                else self.update_data_configuration
            )
            self.import_data_execution_page.setup_sessions(
                configuration,
                self.import_data_file_model.import_sessions(
                    self.data_configuration_page.order_list()
                ),
            )

        if self.current_id == PageIds.ExportDataConfiguration:
            self.export_data_configuration_page.setup_dialog(
                self._basket_handling(self.export_data_configuration)
            )

        if self.current_id == PageIds.ExportDataExecution:
            sessions = {}
            sessions[self.current_export_target] = {}
            models = []
            datasets = []
            baskets = []
            if self.current_export_filter == SchemaDataFilterMode.MODEL:
                models = self.export_models_model.checked_entries()
            elif self.current_export_filter == SchemaDataFilterMode.DATASET:
                datasets = self.export_datasets_model.checked_entries()
            elif self.current_export_filter == SchemaDataFilterMode.BASKET:
                baskets = self.export_baskets_model.checked_entries()
            else:
                # no filter - export all models
                models = self.export_models_model.stringList()

            sessions[self.current_export_target]["models"] = models
            sessions[self.current_export_target]["datasets"] = datasets
            sessions[self.current_export_target]["baskets"] = baskets

            self.export_data_execution_page.setup_sessions(
                self.export_data_configuration, sessions
            )

    def _update_configurations(self, page):
        # update all configurations to have the same settings for all of them
        page.update_configuration(self.import_schema_configuration)
        page.update_configuration(self.import_data_configuration)
        page.update_configuration(self.update_data_configuration)
        page.update_configuration(self.export_data_configuration)
        # and use schema config to save (db settings and the schema settings)
        page.save_configuration(self.import_schema_configuration)

    def _current_page_title(self, id):
        if id == PageIds.ImportSourceSelection:
            return self.tr("Source Selection")
        elif id == PageIds.ImportDatabaseSelection:
            return self.tr("Database Configuration")
        elif id == PageIds.GenerateDatabaseSelection:
            return self.tr("Database Configuration")
        elif id == PageIds.ImportSchemaConfiguration:
            return self.tr("Schema Import Configuration")
        elif id == PageIds.ImportSchemaExecution:
            return self.tr("Schema Import Sessions")
        elif id == PageIds.ImportDataConfiguration:
            return self.tr("Data import configuration")
        elif id == PageIds.ImportDataExecution:
            return self.tr("Data Import Sessions")
        elif id == PageIds.ExportDataConfiguration:
            return self.tr("Data export configuration")
        elif id == PageIds.ExportDataExecution:
            return self.tr("Data export Sessions")
        elif id == PageIds.ProjectCreation:
            return self.tr("Generate a QGIS Project")
        else:
            return self.tr("Model Baker - Workflow Wizard")

    def _basket_handling(self, configuration):
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            return db_connector.get_basket_handling()
        return False

    def _db_or_schema_exists(self, configuration):
        db_connector = db_utils.get_db_connector(configuration)
        if db_connector:
            return db_connector.db_or_schema_exists()
        return False

    def refresh_export_models(self):
        db_connector = db_utils.get_db_connector(self.export_data_configuration)
        self.export_models_model.refresh_model(db_connector)
        self.export_datasets_model.refresh_model(db_connector)
        self.export_baskets_model.refresh_model(db_connector)
        return

    def refresh_import_models(self, silent=False):
        db_connector = db_utils.get_db_connector(self.import_schema_configuration)
        return self.import_models_model.refresh_model(
            self.source_model, db_connector, silent
        )

    def get_topping_file_list(self, id_list):
        topping_file_model = self.get_topping_file_model(id_list)
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                self.log_panel.print_info(
                    self.tr("- - Got file {}").format(file_path), LogColor.COLOR_TOPPING
                )
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, id_list):
        topping_file_cache = IliToppingFileCache(
            self.import_schema_configuration.base_configuration, id_list
        )

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()
        self.log_panel.print_info(self.tr("- - Downloading…"), LogColor.COLOR_TOPPING)

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        if len(topping_file_cache.downloaded_files) == len(id_list):
            self.log_panel.print_info(
                self.tr("- - All topping files successfully downloaded"),
                LogColor.COLOR_TOPPING,
            )
        else:
            missing_file_ids = id_list
            for downloaded_file_id in topping_file_cache.downloaded_files:
                if downloaded_file_id in missing_file_ids:
                    missing_file_ids.remove(downloaded_file_id)
            self.log_panel.print_info(
                self.tr(
                    "- - Some topping files where not successfully downloaded: {}"
                ).format(" ".join(missing_file_ids)),
                LogColor.COLOR_TOPPING,
            )

        return topping_file_cache.model

    def update_referecedata_cache_model(self, filter_models, type):
        # updates the model and waits for the end
        loop = QEventLoop()
        self.ilireferencedatacache.model_refreshed.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(10000)
        self.refresh_referencedata_cache(filter_models, type)
        loop.exec()
        return self.ilireferencedatacache.model

    def refresh_referencedata_cache(self, filter_models, type):
        self.ilireferencedatacache.base_configuration = self.base_config
        self.ilireferencedatacache.filter_models = filter_models
        self.ilireferencedatacache.type = type
        self.ilireferencedatacache.refresh()

    def _db_modelnames(self, configuration):
        db_connector = db_utils.get_db_connector(configuration)
        modelnames = list()
        if db_connector:
            if db_connector.db_or_schema_exists() and db_connector.metadata_exists():
                db_models = db_connector.get_models()
                regex = re.compile(r"(?:\{[^\}]*\}|\s)")
                for db_model in db_models:
                    for modelname in regex.split(db_model["modelname"]):
                        modelnames.append(modelname.strip())
        return modelnames

    def add_source(self, source, origin_info):
        if os.path.isfile(source):
            name = pathlib.Path(source).name
            type = pathlib.Path(source).suffix[1:]
            path = source
        else:
            name = source
            type = "model"
            path = None
        return self.source_model.add_source(name, type, path, origin_info)

    def append_dropped_files(self, dropped_files):
        if dropped_files:
            for dropped_file in dropped_files:
                self.add_source(
                    dropped_file, self.tr("Added by user with drag'n'drop.")
                )


class WorkflowWizardDialog(QDialog):
    def __init__(self, iface, base_config, parent):
        QDialog.__init__(self, parent)
        self.iface = iface
        self.base_config = base_config

        self.setWindowTitle(self.tr("QGIS Model Baker - Workflow Wizard"))
        self.log_panel = LogPanel()
        self.workflow_wizard = WorkflowWizard(self.iface, self.base_config, self)
        self.workflow_wizard.setStartId(PageIds.Intro)
        self.workflow_wizard.setWindowFlags(Qt.Widget)
        self.workflow_wizard.setFixedHeight(600)
        self.workflow_wizard.setMinimumWidth(800)
        self.workflow_wizard.show()

        self.workflow_wizard.finished.connect(self.done)
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.workflow_wizard)
        splitter.addWidget(self.log_panel)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def append_dropped_files(self, dropped_files):
        """
        Appends the files, restarts the wizard and jumps to the next page (what is ImportSourceSelection)
        """
        self.workflow_wizard.append_dropped_files(dropped_files)
        self.workflow_wizard.restart()
        self.workflow_wizard.next()
