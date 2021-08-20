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

from QgisModelBaker.gui.workflow_wizard.import_data_configuration_page import DEFAULT_DATASETNAME
from qgis.PyQt.QtWidgets import (
    QWidget,
    QAction,
    QGridLayout
)
from qgis.PyQt.QtCore import (
    Qt
)
from ...utils import get_ui_class
from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from ...libili2db import iliimporter
from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.gui.edit_command import EditCommandDialog

from QgisModelBaker.libili2db.ili2dbutils import JavaNotFoundError
from QgisModelBaker.utils.qt_utils import OverrideCursor

from qgis.PyQt.QtCore import pyqtSignal

WIDGET_UI = get_ui_class('workflow_wizard/import_session_panel.ui')


class ImportSessionPanel(QWidget, WIDGET_UI):

    print_info = pyqtSignal(str, str)
    on_stderr = pyqtSignal(str)
    on_process_started = pyqtSignal(str)
    on_process_finished = pyqtSignal(int, int)
    on_done_or_skipped = pyqtSignal(object)

    def __init__(self, general_configuration, file, models, dataset, data_import, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        self.file = file
        self.models = models
        self.dataset = dataset

        # set up the gui
        self.create_text = self.tr('Run')
        self.set_button_to_create_action = QAction(self.create_text, None)
        self.set_button_to_create_action.triggered.connect(
            self.set_button_to_create)

        self.create_without_constraints_text = self.tr(
            'Run without constraints')
        self.set_button_to_create_without_constraints_action = QAction(
            self.create_without_constraints_text, None)
        self.set_button_to_create_without_constraints_action.triggered.connect(
            self.set_button_to_create_without_constraints)

        self.edit_command_action = QAction(
            self.tr('Edit ili2db command'), None)
        self.edit_command_action.triggered.connect(self.edit_command)

        self.skip_action = QAction(self.tr('Skip'), None)
        self.skip_action.triggered.connect(self.skip)

        self.create_tool_button.addAction(
            self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.addAction(self.skip_action)
        self.create_tool_button.setText(self.create_text)
        self.create_tool_button.clicked.connect(self.run)

        # set up the values
        self.configuration = general_configuration
        self.data_import = data_import
        if not self.data_import:
            self.configuration.ilifile = ''
            if self.file != 'repository':
                self.configuration.ilifile = self.file
            self.configuration.ilimodels = ';'.join(self.models)
            self.info_label.setText(
                self.tr('Import {}').format(', '.join(self.models)))
        else:
            self.configuration.xtffile = self.file
            self.configuration.ilimodels = ';'.join(self.models)
            self.info_label.setText(self.tr('Import {} of {}').format(
                ', '.join(self.models), self.file))
            self.configuration.dataset = self.dataset

        self.db_simple_factory = DbSimpleFactory()

        self.is_skipped_or_done = False

    @property
    def id(self):
        return (self.file, self.models)

    def set_button_to_create(self):
        """
        Changes the text of the button to create (with validation) and sets the validate_data to true.
        So on clicking the button the creation will start with validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.configuration.disable_validations = False
        self.create_tool_button.removeAction(self.set_button_to_create_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(
            self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_text)

    def set_button_to_create_without_constraints(self):
        """
        Changes the text of the button to create without validation and sets the validate_data to false.
        So on clicking the button the creation will start without validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.configuration.disable_validations = True
        self.create_tool_button.removeAction(
            self.set_button_to_create_without_constraints_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_without_constraints_text)

    def skip(self):
        self.setDisabled(True)
        self.print_info.emit(self.tr('Import skipped!\n'), LogPanel.COLOR_INFO)
        self.is_skipped_or_done = True
        self.on_done_or_skipped.emit(self.id)

    def edit_command(self):
        """
        A dialog opens giving the user the possibility to edit the ili2db command used for the creation
        """
        importer = iliimporter.Importer()
        importer.tool = self.configuration.tool
        importer.configuration = self.configuration
        command = importer.command(True)
        edit_command_dialog = EditCommandDialog(self)
        edit_command_dialog.command_edit.setPlainText(command)
        if edit_command_dialog.exec_():
            edited_command = edit_command_dialog.command_edit.toPlainText()
            self.run(edited_command)

    def run(self, edited_command=None):
        if self.is_skipped_or_done:
            return True

        importer = iliimporter.Importer(dataImport=self.data_import)
        importer.tool = self.configuration.tool
        importer.configuration = self.configuration

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.setValue(10)
            self.setDisabled(True)

            importer.stdout.connect(
                lambda str: self.print_info.emit(str, LogPanel.COLOR_INFO))
            importer.stderr.connect(self.on_stderr)
            importer.process_started.connect(self.on_process_started)
            importer.process_finished.connect(self.on_process_finished)
            self.progress_bar.setValue(20)
            try:
                if importer.run(edited_command) != iliimporter.Importer.SUCCESS:
                    self.progress_bar.setValue(0)
                    self.setDisabled(False)
                    return False
            except JavaNotFoundError as e:
                self.print_info.emit(e.error_string, LogPanel.COLOR_FAIL)
                self.progress_bar.setValue(0)
                self.setDisabled(False)
                return False

            self.progress_bar.setValue(90)
            if not self.data_import and self.configuration.create_basket_col:
                self._create_default_dataset()
            self.progress_bar.setValue(100)
            self.print_info.emit(self.tr('Import done!\n'),
                                 LogPanel.COLOR_SUCCESS)
            self.on_done_or_skipped.emit(self.id)
            self.is_skipped_or_done = True
            return True

    def _create_default_dataset(self):
        self.print_info.emit(self.tr('Create the default dataset {}').format(DEFAULT_DATASETNAME), LogPanel.COLOR_INFO)
        db_connector = self._get_db_connector(self.configuration)

        default_dataset_tid = None
        default_datasets_info_tids = [datasets_info['t_id'] for datasets_info in db_connector.get_datasets_info() if datasets_info['datasetname'] == DEFAULT_DATASETNAME]
        if default_datasets_info_tids:
            default_dataset_tid = default_datasets_info_tids[0]
        else:
            status, message = db_connector.create_dataset(DEFAULT_DATASETNAME)
            self.print_info.emit(message, LogPanel.COLOR_INFO) 
            if status:
                default_datasets_info_tids = [datasets_info['t_id'] for datasets_info in db_connector.get_datasets_info() if datasets_info['datasetname'] == DEFAULT_DATASETNAME]
                if default_datasets_info_tids:
                    default_dataset_tid = default_datasets_info_tids[0]
        
        if default_dataset_tid is not None:
            for topic_record in db_connector.get_topics_info():
                status, message = db_connector.create_basket( default_dataset_tid, '.'.join([topic_record['model'], topic_record['topic']]))
                self.print_info.emit(self.tr('- {}').format(message), LogPanel.COLOR_INFO)                    
        else:
            self.print_info.emit(self.tr('No default dataset created ({}) - do it manually in the dataset manager.').format(message), LogPanel.COLOR_FAIL)

    def _get_db_connector(self, configuration):
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