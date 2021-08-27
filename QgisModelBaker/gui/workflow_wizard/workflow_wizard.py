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

from qgis.PyQt.QtCore import (
    QTimer,
    Qt,
    QEventLoop,
)

from qgis.PyQt.QtWidgets import QWizard, QDialog, QVBoxLayout

from QgisModelBaker.gui.workflow_wizard.wizard_tools import (
    SourceModel,
    ImportDataModel,
    ImportModelsModel,
    ExportDatasetsModel,
    ExportModelsModel,
    TransferExtensions,
)

from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.globals import DbActionType

from QgisModelBaker.libili2db.ilicache import IliToppingFileCache

from QgisModelBaker.libili2db.ili2dbconfig import (
    UpdateDataConfiguration,
    ImportDataConfiguration,
    SchemaImportConfiguration,
    ExportConfiguration,
)

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError

from QgisModelBaker.gui.workflow_wizard.intro_page import IntroPage
from QgisModelBaker.gui.workflow_wizard.import_source_selection_page import (
    ImportSourceSeletionPage,
)
from QgisModelBaker.gui.workflow_wizard.database_selection_page import (
    DatabaseSelectionPage,
)
from QgisModelBaker.gui.workflow_wizard.import_schema_configuration_page import (
    ImportSchemaConfigurationPage,
)
from QgisModelBaker.gui.workflow_wizard.execution_page import ExecutionPage
from QgisModelBaker.gui.workflow_wizard.project_creation_page import ProjectCreationPage
from QgisModelBaker.gui.workflow_wizard.import_data_configuration_page import (
    ImportDataConfigurationPage,
)
from QgisModelBaker.gui.workflow_wizard.export_data_configuration_page import (
    ExportDataConfigurationPage,
)

from ...utils.ui import LogColor

class WorkflowWizard(QWizard):

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

        # configuration objects are keeped on top level to be able to access them from individual pages
        self.import_schema_configuration = SchemaImportConfiguration()
        self.import_data_configuration = ImportDataConfiguration()
        self.update_data_configuration = UpdateDataConfiguration()
        self.export_data_configuration = ExportConfiguration()
        self.import_schema_configuration.base_configuration = base_config
        self.import_data_configuration.base_configuration = base_config
        self.update_data_configuration.base_configuration = base_config
        self.export_data_configuration.base_configuration = base_config

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

        # the export_models_model keeps every single model found in the current database and a checked state
        self.export_models_model = ExportModelsModel()
        # the export_datasets_models keeps every dataset found in the current database and keeps the selected dataset
        self.export_datasets_model = ExportDatasetsModel()
        # the current export target is the current set target file for the export. It's keeped top level to have a consequent behavior of those information.
        self.current_export_target = ""

        # pages setup
        self.intro_page = IntroPage(self, self._current_page_title(self.Page_Intro_Id))
        self.source_seletion_page = ImportSourceSeletionPage(
            self, self._current_page_title(self.Page_ImportSourceSeletion_Id)
        )
        self.import_database_seletion_page = DatabaseSelectionPage(
            self,
            self._current_page_title(self.Page_ImportDatabaseSelection_Id),
            DbActionType.IMPORT_DATA,
        )
        self.schema_configuration_page = ImportSchemaConfigurationPage(
            self, self._current_page_title(self.Page_ImportSchemaConfiguration_Id)
        )
        self.import_schema_execution_page = ExecutionPage(
            self,
            self._current_page_title(self.Page_ImportSchemaExecution_Id),
            DbActionType.GENERATE,
        )
        self.data_configuration_page = ImportDataConfigurationPage(
            self, self._current_page_title(self.Page_ImportDataConfiguration_Id)
        )
        self.import_data_execution_page = ExecutionPage(
            self,
            self._current_page_title(self.Page_ImportDataExecution_Id),
            DbActionType.IMPORT_DATA,
        )
        self.project_creation_page = ProjectCreationPage(
            self, self._current_page_title(self.Page_ProjectCreation_Id)
        )
        self.generate_database_seletion_page = DatabaseSelectionPage(
            self,
            self._current_page_title(self.Page_GenerateDatabaseSelection_Id),
            DbActionType.GENERATE,
        )
        self.export_database_seletion_page = DatabaseSelectionPage(
            self,
            self._current_page_title(self.Page_ExportDatabaseSelection_Id),
            DbActionType.EXPORT,
        )
        self.export_data_configuration_page = ExportDataConfigurationPage(
            self, self._current_page_title(self.Page_ExportDataConfiguration_Id)
        )
        self.export_data_execution_page = ExecutionPage(
            self,
            self._current_page_title(self.Page_ExportDataExecution_Id),
            DbActionType.EXPORT,
        )
        self.setPage(self.Page_Intro_Id, self.intro_page)
        self.setPage(self.Page_ImportSourceSeletion_Id, self.source_seletion_page)
        self.setPage(
            self.Page_ImportDatabaseSelection_Id, self.import_database_seletion_page
        )
        self.setPage(
            self.Page_ImportSchemaConfiguration_Id, self.schema_configuration_page
        )
        self.setPage(
            self.Page_ImportSchemaExecution_Id, self.import_schema_execution_page
        )
        self.setPage(self.Page_ImportDataConfiguration_Id, self.data_configuration_page)
        self.setPage(self.Page_ImportDataExecution_Id, self.import_data_execution_page)
        self.setPage(self.Page_ProjectCreation_Id, self.project_creation_page)
        self.setPage(
            self.Page_GenerateDatabaseSelection_Id, self.generate_database_seletion_page
        )
        self.setPage(
            self.Page_ExportDatabaseSelection_Id, self.export_database_seletion_page
        )
        self.setPage(
            self.Page_ExportDataConfiguration_Id, self.export_data_configuration_page
        )
        self.setPage(self.Page_ExportDataExecution_Id, self.export_data_execution_page)

        self.currentIdChanged.connect(self.id_changed)

    def next_id(self):
        # this is called on the nextId overrides of the pages - so after the next-button is pressed
        # it finalizes the edits on the current page and returns the evaluated id of the next page
        if self.current_id == self.Page_ImportSourceSeletion_Id:
            return self.Page_ImportDatabaseSelection_Id

        if self.current_id == self.Page_ImportDatabaseSelection_Id:
            self._update_configurations(self.import_database_seletion_page)
            if self.refresh_import_models(True):
                # when there are models to import, we go to the configuration page for schema import
                return self.Page_ImportSchemaConfiguration_Id
            if self.import_data_file_model.rowCount():
                # when there are transfer files found, we go to the configuration page for data import
                return self.Page_ImportDataConfiguration_Id
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_GenerateDatabaseSelection_Id:
            self._update_configurations(self.generate_database_seletion_page)
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_ExportDatabaseSelection_Id:
            self._update_configurations(self.export_database_seletion_page)
            return self.Page_ExportDataConfiguration_Id

        if self.current_id == self.Page_ImportSchemaConfiguration_Id:
            self.schema_configuration_page.update_configuration(
                self.import_schema_configuration
            )
            self.schema_configuration_page.save_configuration(
                self.import_schema_configuration
            )
            if bool(self.import_models_model.checked_models()):
                return self.Page_ImportSchemaExecution_Id
            if self.import_data_file_model.rowCount():
                return self.Page_ImportDataConfiguration_Id
            else:
                self.log_panel.print_info(
                    self.tr(f"No models, no transfer files, nothing to do...")
                )

        if self.current_id == self.Page_ImportSchemaExecution_Id:
            if self.import_data_file_model.rowCount():
                return self.Page_ImportDataConfiguration_Id
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_ImportDataConfiguration_Id:
            return self.Page_ImportDataExecution_Id

        if self.current_id == self.Page_ImportDataExecution_Id:
            return self.Page_ProjectCreation_Id

        if self.current_id == self.Page_ExportDataConfiguration_Id:
            return self.Page_ExportDataExecution_Id

        return self.current_id

    def id_changed(self, new_id):
        self.current_id = new_id

        self.log_panel.print_info(
            self.tr(f" > ---------- {self._current_page_title(self.current_id)}")
        )

        if self.current_id == self.Page_ImportDatabaseSelection_Id:
            # use schema config to restore
            self.import_database_seletion_page.restore_configuration(
                self.import_schema_configuration
            )

        if self.current_id == self.Page_GenerateDatabaseSelection_Id:
            self.generate_database_seletion_page.restore_configuration(
                self.import_schema_configuration
            )

        if self.current_id == self.Page_ExportDatabaseSelection_Id:
            self.export_database_seletion_page.restore_configuration(
                self.export_data_configuration
            )

        if self.current_id == self.Page_ImportSchemaConfiguration_Id:
            self.refresh_import_models()
            self.schema_configuration_page.restore_configuration()

        if self.current_id == self.Page_ImportSchemaExecution_Id:
            self.import_schema_execution_page.setup_sessions(
                self.import_schema_configuration,
                self.import_models_model.import_sessions(),
            )

        if self.current_id == self.Page_ProjectCreation_Id:
            self.project_creation_page.set_configuration(
                self.import_schema_configuration
            )

        if self.current_id == self.Page_ImportDataConfiguration_Id:
            self.data_configuration_page.setup_dialog(self._basket_handling())

        if self.current_id == self.Page_ImportDataExecution_Id:
            configuration = self.import_data_configuration if not self._basket_handling() else self.update_data_configuration
            self.import_data_execution_page.setup_sessions(
                configuration,
                self.import_data_file_model.import_sessions(
                    self.data_configuration_page.order_list()
                ),
            )

        if self.current_id == self.Page_ExportDataConfiguration_Id:
            self.refresh_export_models()
            self.export_data_configuration_page.setup_dialog(self._basket_handling())


        if self.current_id == self.Page_ExportDataExecution_Id:
            sessions = {}
            sessions[self.current_export_target] = {}
            sessions[self.current_export_target][
                "models"
            ] = self.export_models_model.checked_entries()
            sessions[self.current_export_target][
                "datasets"
            ] = self.export_datasets_model.checked_entries()
            self.export_data_execution_page.setup_sessions(
                self.export_data_configuration, sessions
            )

    def _update_configurations(self, page ):
        # update all configurations to have the same db settings for all of them
        page.update_configuration(
            self.import_schema_configuration
        )
        page.update_configuration(
            self.import_data_configuration
        )
        page.update_configuration(
            self.update_data_configuration
        )
        page.update_configuration(
            self.export_data_configuration
        )
        # and use schema config to save
        page.save_configuration(
            self.import_schema_configuration
        )

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

    def _basket_handling(self):
        db_connector = self.get_db_connector(
            self.import_data_configuration
        )
        return db_connector.get_basket_handling()

    def refresh_export_models(self):
        db_connector = self.get_db_connector(self.export_data_configuration)
        self.export_models_model.refresh_model(db_connector)
        self.export_datasets_model.refresh_model(db_connector)
        return

    def refresh_import_models(self, silent=False):
        db_connector = self.get_db_connector(self.import_schema_configuration)
        return self.import_models_model.refresh_model(
            self.source_model, db_connector, silent
        )

    def get_db_connector(self, configuration):
        # migth be moved to db_utils...
        db_simple_factory = DbSimpleFactory()
        schema = configuration.dbschema

        db_factory = db_simple_factory.create_factory(configuration.tool)
        config_manager = db_factory.get_db_command_config_manager(configuration)
        uri_string = config_manager.get_uri(configuration.db_use_super_login)

        try:
            return db_factory.get_db_connector(uri_string, schema)
        except (DBConnectorError, FileNotFoundError):
            return None

    def get_topping_file_list(self, id_list, log_panel):
        topping_file_model = self.get_topping_file_model(id_list, log_panel)
        file_path_list = []

        for file_id in id_list:
            matches = topping_file_model.match(
                topping_file_model.index(0, 0), Qt.DisplayRole, file_id, 1
            )
            if matches:
                file_path = matches[0].data(int(topping_file_model.Roles.LOCALFILEPATH))
                log_panel.print_info(
                    self.tr("- - Got file {}").format(file_path), LogColor.COLOR_TOPPING
                )
                file_path_list.append(file_path)
        return file_path_list

    def get_topping_file_model(self, id_list, log_panel):
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
        log_panel.print_info(self.tr("- - Downloading…"), LogColor.COLOR_TOPPING)

        if len(topping_file_cache.downloaded_files) != len(id_list):
            loop.exec()

        if len(topping_file_cache.downloaded_files) == len(id_list):
            log_panel.print_info(
                self.tr("- - All topping files successfully downloaded"),
                LogColor.COLOR_TOPPING,
            )
        else:
            missing_file_ids = id_list
            for downloaded_file_id in topping_file_cache.downloaded_files:
                if downloaded_file_id in missing_file_ids:
                    missing_file_ids.remove(downloaded_file_id)
            log_panel.print_info(
                self.tr(
                    "- - Some topping files where not successfully downloaded: {}"
                ).format(" ".join(missing_file_ids)),
                LogColor.COLOR_TOPPING,
            )

        return topping_file_cache.model


class WorkflowWizardDialog(QDialog):
    def __init__(self, iface, base_config, parent=None):
        QDialog.__init__(self)
        self.iface = iface
        self.base_config = base_config

        self.setWindowTitle(self.tr("QGIS Model Baker - Workflow Wizard"))
        self.log_panel = LogPanel()
        self.workflow_wizard = WorkflowWizard(self.iface, self.base_config, self)
        self.workflow_wizard.setStartId(self.workflow_wizard.Page_Intro_Id)
        self.workflow_wizard.setWindowFlags(Qt.Widget)
        self.workflow_wizard.show()

        self.workflow_wizard.finished.connect(self.done)
        layout = QVBoxLayout()
        layout.addWidget(self.workflow_wizard)
        layout.addWidget(self.log_panel)
        self.setLayout(layout)
