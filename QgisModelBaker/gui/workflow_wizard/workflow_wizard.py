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
import logging
import os
import pathlib
import re

from qgis.PyQt.QtCore import QEventLoop, QSize, Qt, QTimer
from qgis.PyQt.QtGui import QPixmap
from qgis.PyQt.QtWidgets import QDialog, QSplitter, QVBoxLayout, QWizard

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.log_panel import LogPanel
from QgisModelBaker.gui.workflow_wizard.database_selection_page import (
    DatabaseSelectionPage,
)
from QgisModelBaker.gui.workflow_wizard.default_baskets_page import DefaultBasketsPage
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
from QgisModelBaker.gui.workflow_wizard.tid_configuration_page import (
    TIDConfigurationPage,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ili2dbconfig import (
    ExportConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
    UpdateDataConfiguration,
)
from QgisModelBaker.libs.modelbaker.iliwrapper.ilicache import (
    IliDataCache,
    IliToppingFileCache,
)
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType
from QgisModelBaker.utils import gui_utils
from QgisModelBaker.utils.gui_utils import (
    FileDropListView,
    ImportDataModel,
    ImportModelsModel,
    LogLevel,
    PageIds,
    SchemaBasketsModel,
    SchemaDataFilterMode,
    SchemaDatasetsModel,
    SchemaModelsModel,
    SourceModel,
    TransferExtensions,
)


class WorkflowWizard(QWizard):
    def __init__(self, iface, base_config, parent):
        QWizard.__init__(self, parent)

        self.setWindowTitle(self.tr("QGIS Model Baker Wizard"))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOptions(
            QWizard.WizardOption.NoCancelButtonOnLastPage
            | QWizard.WizardOption.HaveHelpButton
        )

        self.current_id = 0

        self.iface = iface
        self.log_panel = parent.log_panel
        self.wizard_dialog = parent

        # configuration objects are keeped on top level to be able to access them from individual pages
        self.base_config = base_config
        self.import_schema_configuration = SchemaImportConfiguration()
        self.import_schema_configuration.create_basket_col = True
        self.import_data_configuration = ImportDataConfiguration()
        self.update_data_configuration = UpdateDataConfiguration()
        self.export_data_configuration = ExportConfiguration()
        self.import_schema_configuration.base_configuration = self.base_config
        self.import_data_configuration.base_configuration = self.base_config
        self.update_data_configuration.base_configuration = self.base_config
        self.update_data_configuration.with_importbid = True
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
        self.import_data_file_model.setFilterRegularExpression(
            "|".join(TransferExtensions)
        )
        self.ilireferencedatacache = IliDataCache(
            self.import_schema_configuration.base_configuration,
            "referenceData",
        )
        self.ilireferencedatacache.new_message.connect(self.log_panel.show_message)

        # the current_models_model keeps every single model found in the current database and keeps the selected models
        self.current_models_model = SchemaModelsModel()
        # the current_datasets_model keeps every dataset found in the current database and keeps the selected dataset
        self.current_datasets_model = SchemaDatasetsModel()
        # the current_baskets_model keeps every baskets found in the current database and keeps the selected baskets
        self.current_baskets_model = SchemaBasketsModel()

        # the current export target is the current set target file for the export. It's keeped top level to have a consequent behavior of those information.
        self.current_export_target = ""
        self.current_filter_mode = SchemaDataFilterMode.NO_FILTER

        # the current_export_models_model keeps every single model found in the current database and keeps the selected models
        self.current_export_models_model = SchemaModelsModel()
        self.current_export_models_active = False

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
            DbActionType.SCHEMA_IMPORT,
        )
        self.default_baskets_page = DefaultBasketsPage(
            self, self._current_page_title(PageIds.DefaultBaskets)
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
        self.tid_configuration_page = TIDConfigurationPage(
            self, self._current_page_title(PageIds.TIDConfiguration)
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
        self.setPage(PageIds.DefaultBaskets, self.default_baskets_page)
        self.setPage(PageIds.ImportDataConfiguration, self.data_configuration_page)
        self.setPage(PageIds.ImportDataExecution, self.import_data_execution_page)
        self.setPage(PageIds.ProjectCreation, self.project_creation_page)
        self.setPage(PageIds.TIDConfiguration, self.tid_configuration_page)
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

        # on pressing the help button
        self.helpRequested.connect(self._show_help)

        self.source_selection_page.quick_visualize_button.clicked.connect(
            self.gather_files_and_leave_to_quick_visualizer
        )

    def gather_files_and_leave_to_quick_visualizer(self):
        self.wizard_dialog.prefer_quickvisualizer(self.import_data_file_model.sources())

    def sizeHint(self):
        return QSize(
            self.fontMetrics().lineSpacing() * 48, self.fontMetrics().lineSpacing() * 48
        )

    def next_id(self):
        """
        This is called on the nextId overrides of the pages - so after the next-button is pressed.
        It finalizes the edits on the current page and returns the evaluated id of the next page.
        """

        # This function is called multiple times. As well it's called on pressing "Back". It's not really clear why. That's why it checks if the current page is the one the last current_id has been stored for, to be sure it only proceeds on pressing "Next".
        if self.current_id == self.currentId():
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
                            self.tr("Database or schema not reachable.")
                        )

            if self.current_id == PageIds.ExportDatabaseSelection:
                if self.export_database_selection_page.is_valid():
                    self._update_configurations(self.export_database_selection_page)
                    if self._db_or_schema_exists(self.export_data_configuration):
                        self.refresh_export_models()
                        return PageIds.ExportDataConfiguration
                    else:
                        self.log_panel.print_info(
                            self.tr("Database or schema not reachable.")
                        )

            if self.current_id == PageIds.ImportSchemaConfiguration:
                self._update_configurations(self.schema_configuration_page)
                if bool(self.import_models_model.checked_models()):
                    return PageIds.ImportSchemaExecution
                self.log_panel.print_info(
                    self.tr(
                        "Checking for potential referenced data on the repositories (might take a while)..."
                    )
                )
                self.busy(
                    self.schema_configuration_page,
                    True,
                    self.tr("Checking for potential referenced data..."),
                )
                self.schema_configuration_page.setComplete(False)
                if (
                    self.import_data_file_model.rowCount()
                    or self.update_referecedata_cache_model(
                        self._db_modelnames(self.import_data_configuration),
                        "referenceData",
                    ).rowCount()
                ):
                    self.log_panel.print_info(
                        self.tr("Potential referenced data found.")
                    )
                    self.schema_configuration_page.setComplete(True)
                    self.busy(self.schema_configuration_page, False)
                    return PageIds.ImportDataConfiguration
                else:
                    self.log_panel.print_info(
                        self.tr(
                            "No models, no transfer files and no potential referenced data found. Nothing to do."
                        )
                    )
                    self.schema_configuration_page.setComplete(True)
                    self.busy(self.schema_configuration_page, False)

            if self.current_id == PageIds.ImportSchemaExecution:
                # if basket handling active, go to the create basket
                if self._basket_handling(self.import_schema_configuration):
                    return PageIds.DefaultBaskets

                # if transfer files available, then go to data import
                if self.import_data_file_model.rowCount():
                    return PageIds.ImportDataConfiguration

                # if transfer file are possible (by getting via Repositories), go to the data import
                self.log_panel.print_info(
                    self.tr(
                        "Checking for potential referenced data on the repositories (might take a while)..."
                    )
                )
                self.busy(
                    self.import_schema_execution_page,
                    True,
                    self.tr("Checking for potential referenced data..."),
                )
                self.import_schema_execution_page.setComplete(False)
                if self.update_referecedata_cache_model(
                    self._db_modelnames(self.import_data_configuration),
                    "referenceData",
                ).rowCount():
                    self.log_panel.print_info(
                        self.tr("Potential referenced data found.")
                    )
                    self.import_schema_execution_page.setComplete(True)
                    self.busy(self.import_schema_execution_page, False)
                    return PageIds.ImportDataConfiguration
                self.import_schema_execution_page.setComplete(True)
                self.busy(self.import_schema_execution_page, False)

                # otherwise, go to project create
                return PageIds.ProjectCreation

            if self.current_id == PageIds.DefaultBaskets:
                # if transfer files available, then go to data import
                if self.import_data_file_model.rowCount():
                    return PageIds.ImportDataConfiguration

                # if transfer file are possible (by getting via Repositories), go to the data import
                self.log_panel.print_info(
                    self.tr(
                        "Checking for potential referenced data on the repositories (might take a while)..."
                    )
                )
                self.default_baskets_page.setComplete(False)
                self.busy(
                    self.default_baskets_page,
                    True,
                    self.tr("Checking for potential referenced data..."),
                )
                if self.update_referecedata_cache_model(
                    self._db_modelnames(self.import_data_configuration),
                    "referenceData",
                ).rowCount():
                    self.log_panel.print_info(
                        self.tr("Potential referenced data found.")
                    )
                    self.default_baskets_page.setComplete(True)
                    self.busy(self.default_baskets_page, False)
                    return PageIds.ImportDataConfiguration
                self.default_baskets_page.setComplete(True)
                self.busy(self.default_baskets_page, False)

                # otherwise, go to project create
                return PageIds.ProjectCreation

            if self.current_id == PageIds.ImportDataConfiguration:
                if self.import_data_file_model.rowCount():
                    self._update_configurations(self.data_configuration_page)
                    return PageIds.ImportDataExecution
                else:
                    return PageIds.ProjectCreation

            if self.current_id == PageIds.ImportDataExecution:
                return PageIds.ProjectCreation

            if self.current_id == PageIds.ExportDataConfiguration:
                return PageIds.ExportDataExecution

            if self.current_id == PageIds.ProjectCreation:
                return PageIds.TIDConfiguration

        return self.current_id

    def id_changed(self, new_id):
        self.current_id = new_id

        self.log_panel.print_info(
            self.tr(f" > ---------- {self._current_page_title(self.current_id)}")
        )

        if self.current_id == PageIds.ImportSourceSelection:
            # Add extra buttons
            # Clear cache
            self.setOption(QWizard.HaveCustomButton1, True)
            self.setButton(
                QWizard.CustomButton1, self.source_selection_page.quick_visualize_button
            )
            # Quick import
            self.setOption(QWizard.HaveCustomButton2, True)
            self.setButton(
                QWizard.CustomButton2, self.source_selection_page.clear_cache_button
            )
        else:
            # Remove extra buttons
            # Clear cache
            if (
                self.button(QWizard.CustomButton1)
                == self.source_selection_page.quick_visualize_button
            ):
                self.setOption(QWizard.HaveCustomButton1, False)
            # Quick import
            if (
                self.button(QWizard.CustomButton2)
                == self.source_selection_page.clear_cache_button
            ):
                self.setOption(QWizard.HaveCustomButton2, False)

        if self.current_id == PageIds.ImportDatabaseSelection:
            # use schema config to restore
            self.import_database_selection_page.restore_configuration(
                self.import_schema_configuration, True
            )

        if self.current_id == PageIds.GenerateDatabaseSelection:
            self.generate_database_selection_page.restore_configuration(
                self.import_schema_configuration, True
            )

        if self.current_id == PageIds.ExportDatabaseSelection:
            self.export_database_selection_page.restore_configuration(
                self.export_data_configuration, True
            )

        if self.current_id == PageIds.ImportSchemaConfiguration:
            self.schema_configuration_page.restore_configuration()

        if self.current_id == PageIds.ImportSchemaExecution:
            self.import_schema_execution_page.setup_sessions(
                self.import_schema_configuration,
                self.import_models_model.import_sessions(),
            )

        if self.current_id == PageIds.DefaultBaskets:
            self.default_baskets_page.restore_configuration(
                self.import_schema_configuration
            )

        if self.current_id == PageIds.ProjectCreation:
            self.project_creation_page.restore_configuration(
                self.import_schema_configuration
            )

        if self.current_id == PageIds.TIDConfiguration:
            self.tid_configuration_page.set_configuration(
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
            export_models = []
            if self.current_filter_mode == SchemaDataFilterMode.MODEL:
                models = self.current_models_model.checked_entries()
            elif self.current_filter_mode == SchemaDataFilterMode.DATASET:
                datasets = self.current_datasets_model.checked_entries()
            elif self.current_filter_mode == SchemaDataFilterMode.BASKET:
                baskets = self.current_baskets_model.checked_entries()
            else:
                # no filter - export all models
                models = self.current_models_model.stringList()

            if self.current_export_models_active:
                export_models = self.current_export_models_model.checked_entries()

            sessions[self.current_export_target]["models"] = models
            sessions[self.current_export_target]["datasets"] = datasets
            sessions[self.current_export_target]["baskets"] = baskets
            sessions[self.current_export_target]["export_models"] = export_models

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
        elif (
            id == PageIds.ImportDatabaseSelection
            or id == PageIds.ExportDatabaseSelection
            or id == PageIds.GenerateDatabaseSelection
        ):
            return self.tr("Database Configuration")
        elif id == PageIds.ImportSchemaConfiguration:
            return self.tr("Schema Import Configuration")
        elif id == PageIds.ImportSchemaExecution:
            return self.tr("Schema Import Sessions")
        elif id == PageIds.DefaultBaskets:
            return self.tr("Create Baskets for Default Dataset")
        elif id == PageIds.ImportDataConfiguration:
            return self.tr("Data Import Configuration")
        elif id == PageIds.ImportDataExecution:
            return self.tr("Data Import Sessions")
        elif id == PageIds.ExportDataConfiguration:
            return self.tr("Data Export Configuration")
        elif id == PageIds.ExportDataExecution:
            return self.tr("Data Export Sessions")
        elif id == PageIds.ProjectCreation:
            return self.tr("Generate a QGIS Project")
        elif id == PageIds.TIDConfiguration:
            return self.tr("Configure OID Generation")
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
        self.current_models_model.refresh_model([db_connector])
        self.current_datasets_model.refresh_model(db_connector)
        self.current_baskets_model.refresh_model(db_connector)
        self.current_export_models_model.refresh_model([db_connector])
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
                topping_file_model.index(0, 0), Qt.ItemDataRole.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                self.log_panel.print_info(
                    self.tr("- - Got file {}").format(file_path), LogLevel.TOPPING
                )
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, id_list):
        topping_file_cache = IliToppingFileCache(
            self.import_schema_configuration.base_configuration, id_list
        )

        # we wait for the download or we timeout after 30 seconds and we apply what we have
        loop = QEventLoop()
        topping_file_cache.download_finished_and_model_fresh.connect(
            lambda: loop.quit()
        )
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(30000)

        topping_file_cache.refresh()
        self.log_panel.print_info(self.tr("- - Downloading…"), LogLevel.TOPPING)

        # we wait for the download_finished_and_model_fresh signal, because even when the files are local, it should only continue when both is ready
        loop.exec()

        if len(topping_file_cache.downloaded_files) == len(id_list):
            self.log_panel.print_info(
                self.tr("- - All topping files successfully downloaded"),
                LogLevel.TOPPING,
            )
        else:
            missing_file_ids = id_list
            for downloaded_file_id in topping_file_cache.downloaded_files:
                if downloaded_file_id in missing_file_ids:
                    missing_file_ids.remove(downloaded_file_id)
            try:
                self.log_panel.print_info(
                    self.tr(
                        "- - Some topping files where not successfully downloaded: {}"
                    ).format(" ".join(missing_file_ids)),
                    LogLevel.TOPPING,
                )
            except Exception:
                pass

        return topping_file_cache.model

    def update_referecedata_cache_model(self, filter_models, type):
        # updates the model and waits for the end
        loop = QEventLoop()
        self.ilireferencedatacache.model_refreshed.connect(lambda: loop.quit())
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: loop.quit())
        timer.start(2000)
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

    def remove_sources(self, indices):
        # if it's a ini/toml file that should be removed, then remove it from the config
        if (
            indices[0].data(int(SourceModel.Roles.TYPE))
            in FileDropListView.ValidIniExtensions
        ):
            self.schema_configuration_page.ili2db_options.set_toml_file("")
        return self.source_model.remove_sources(indices)

    def append_dropped_files(self, dropped_files, dropped_ini_files):
        if dropped_files or dropped_ini_files:
            for dropped_file in dropped_files + dropped_ini_files:
                self.add_source(
                    dropped_file, self.tr("Added by user with drag'n'drop.")
                )

        if dropped_ini_files:
            if len(dropped_ini_files) > 1:
                logging.warning(
                    "Only one INI/TOML file is supported by drag&drop: {}".format(
                        dropped_ini_files
                    )
                )

            self.schema_configuration_page.ili2db_options.set_toml_file(
                dropped_ini_files[0]
            )

    def _show_help(self):
        current_id = self.currentId()
        title = self.tr("Help at {}".format(self._current_page_title(current_id)))
        logline, help_paragraphs, docutext = self.currentPage().help_text()
        text = """<hr>
        {help_paragraphs}
        <hr>
        {docu_and_community_paragraphs}
        """.format(
            help_paragraphs=help_paragraphs,
            docutext=docutext,
            docu_and_community_paragraphs=self.tr(
                """
            <p align="justify">{docutext}</p>
            <p align="justify">...or get community help at {forum} or at {github}</p>
            """
            ).format(
                docutext=docutext,
                forum='<a href="https://interlis.discourse.group/c/interlis-werkzeuge/qgis-model-baker">Model Baker @ INTERLIS Forum</a>',
                github='<a href="https://github.com/opengisch/QgisModelBaker/issues">GitHub</a>',
            ),
        )
        log_paragraph = f'<p align="justify"><b><code>&lt; {logline}</code></b></p>'

        self.help_dlg = HelpDialog(self, title, log_paragraph, text)
        self.help_dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.help_dlg.show()

    def busy(self, page, busy, text="Busy..."):
        page.setEnabled(not busy)
        self.log_panel.busy_bar.setVisible(busy)
        if busy:
            self.log_panel.busy_bar.setFormat(text)
        else:
            self.log_panel.scrollbar.setValue(self.log_panel.scrollbar.maximum())


class WorkflowWizardDialog(QDialog):
    def __init__(self, iface, base_config, main_window, parent):
        QDialog.__init__(self, main_window)
        self.setStyleSheet(gui_utils.DEFAULT_STYLE)
        self.iface = iface
        self.base_config = base_config
        self.parent = parent

        self.setWindowTitle(self.tr("Model Baker - Workflow Wizard"))
        self.log_panel = LogPanel()
        self.workflow_wizard = WorkflowWizard(self.iface, self.base_config, self)
        self.workflow_wizard.setStartId(PageIds.Intro)
        self.workflow_wizard.setWindowFlags(Qt.WindowType.Widget)
        self.workflow_wizard.show()
        self.workflow_wizard.finished.connect(self.done)

        self.dropped_files = []

        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.workflow_wizard)
        splitter.addWidget(self.log_panel)
        layout.addWidget(splitter)
        self.setLayout(layout)

    def append_dropped_files(self, dropped_files, dropped_ini_files):
        """
        Appends the files, restarts the wizard and jumps to the next page (what is ImportSourceSelection)
        """
        self.dropped_files = dropped_files
        self.workflow_wizard.append_dropped_files(dropped_files, dropped_ini_files)
        self.workflow_wizard.restart()
        self.workflow_wizard.next()

    def prefer_quickvisualizer(self, files):
        self.accept()
        self.parent.visualize_dropped_files_quickly(files)


class HelpDialog(QDialog, gui_utils.get_ui_class("help_dialog.ui")):
    def __init__(
        self,
        parent=None,
        title="Help",
        logline="I need somebody",
        text="Not just anybody",
    ):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.setWindowTitle(title)
        scaled_pixmap = QPixmap(
            os.path.join(
                os.path.dirname(__file__), "../../images/QgisModelBaker-icon.svg"
            )
        ).scaled(
            int(self.fontMetrics().lineSpacing() * 4.5),
            self.fontMetrics().lineSpacing() * 5,
        )

        self.imagelabel.setPixmap(scaled_pixmap)
        self.loglinelabel.setText(logline)
        self.textlabel.setText(text)
