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

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QAction, QWidget

import QgisModelBaker.gui.workflow_wizard.wizard_tools as wizard_tools
import QgisModelBaker.utils.db_utils as db_utils
from QgisModelBaker.gui.edit_command import EditCommandDialog
from QgisModelBaker.libili2db.globals import DbActionType
from QgisModelBaker.libili2db.ili2dbutils import JavaNotFoundError
from QgisModelBaker.utils.qt_utils import OverrideCursor

from ...libili2db import iliexecutable, iliexporter, iliimporter
from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...utils.ui import LogColor, get_ui_class

WIDGET_UI = get_ui_class("workflow_wizard/session_panel.ui")


class SessionPanel(QWidget, WIDGET_UI):

    print_info = pyqtSignal(str, str)
    on_stderr = pyqtSignal(str)
    on_process_started = pyqtSignal(str)
    on_process_finished = pyqtSignal(int, int)
    on_done_or_skipped = pyqtSignal(object)

    def __init__(
        self, general_configuration, file, models, datasets, db_action_type, parent=None
    ):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        self.file = file
        self.models = models
        self.datasets = datasets

        # set up the gui
        self.create_text = self.tr("Run")
        self.set_button_to_create_action = QAction(self.create_text, None)
        self.set_button_to_create_action.triggered.connect(self.set_button_to_create)

        self.create_without_constraints_text = self.tr("Run without constraints")
        self.set_button_to_create_without_constraints_action = QAction(
            self.create_without_constraints_text, None
        )
        self.set_button_to_create_without_constraints_action.triggered.connect(
            self.set_button_to_create_without_constraints
        )

        self.edit_command_action = QAction(self.tr("Edit ili2db command"), None)
        self.edit_command_action.triggered.connect(self.edit_command)

        self.skip_action = QAction(self.tr("Skip"), None)
        self.skip_action.triggered.connect(self.skip)

        self.create_tool_button.addAction(
            self.set_button_to_create_without_constraints_action
        )
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.addAction(self.skip_action)
        self.create_tool_button.setText(self.create_text)
        self.create_tool_button.clicked.connect(self.run)

        # set up the values
        self.configuration = general_configuration
        self.db_action_type = db_action_type
        if self.db_action_type == DbActionType.GENERATE:
            self.configuration.ilifile = ""
            if self.file != "repository":
                self.configuration.ilifile = self.file
            self.configuration.ilimodels = ";".join(self.models)
            self.info_label.setText(self.tr("Import {}").format(", ".join(self.models)))
        elif self.db_action_type == DbActionType.IMPORT_DATA:
            self.configuration.xtffile = self.file
            self.configuration.ilimodels = ";".join(self.models)
            self.info_label.setText(
                self.tr("Import {} of {}").format(", ".join(self.models), self.file)
            )
            self.configuration.dataset = self.datasets[0] if self.datasets else None
        elif self.db_action_type == DbActionType.EXPORT:
            self.configuration.xtffile = self.file
            self.configuration.ilimodels = ";".join(self.models)
            self.info_label.setText(
                self.tr("Export {} of {} into {}").format(
                    ", ".join(self.models), ", ".join(self.datasets), self.file
                )
            )
            self.configuration.dataset = ";".join(self.datasets)

        self.db_simple_factory = DbSimpleFactory()

        self.is_skipped_or_done = False

    @property
    def id(self):
        return (self.file, self.models, self.datasets)

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
            self.set_button_to_create_without_constraints_action
        )
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
            self.set_button_to_create_without_constraints_action
        )
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_without_constraints_text)

    def skip(self):
        self.setDisabled(True)
        self.print_info.emit(f'{self.tr("Import skipped!")}\n', LogColor.COLOR_INFO)
        self.is_skipped_or_done = True
        self.on_done_or_skipped.emit(self.id)

    def _get_porter(self):
        porter = None
        if self.db_action_type == DbActionType.EXPORT:
            porter = iliexporter.Exporter()
        elif self.db_action_type == DbActionType.IMPORT_DATA:
            porter = iliimporter.Importer(dataImport=True)
        else:
            porter = iliimporter.Importer()
        if porter:
            porter.tool = self.configuration.tool
            porter.configuration = self.configuration
        return porter

    def edit_command(self):
        """
        A dialog opens giving the user the possibility to edit the ili2db command used for the creation
        """
        porter = self._get_porter()
        command = porter.command(True)
        edit_command_dialog = EditCommandDialog(self)
        edit_command_dialog.command_edit.setPlainText(command)
        if edit_command_dialog.exec_():
            edited_command = edit_command_dialog.command_edit.toPlainText()
            self.run(edited_command)

    def run(self, edited_command=None):
        if self.is_skipped_or_done:
            return True

        porter = self._get_porter()

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.setValue(10)
            self.setDisabled(True)

            porter.stdout.connect(
                lambda str: self.print_info.emit(str, LogColor.COLOR_INFO)
            )
            porter.stderr.connect(self.on_stderr)
            porter.process_started.connect(self.on_process_started)
            porter.process_finished.connect(self.on_process_finished)
            self.progress_bar.setValue(20)
            try:
                if porter.run(edited_command) != iliexecutable.IliExecutable.SUCCESS:
                    self.progress_bar.setValue(0)
                    self.setDisabled(False)
                    return False
            except JavaNotFoundError as e:
                self.print_info.emit(e.error_string, LogColor.COLOR_FAIL)
                self.progress_bar.setValue(0)
                self.setDisabled(False)
                return False

            self.progress_bar.setValue(90)
            if (
                self.db_action_type == DbActionType.GENERATE
                and self.configuration.create_basket_col
            ):
                self._create_default_dataset()
            self.progress_bar.setValue(100)
            self.print_info.emit(f'{self.tr("Done!")}\n', LogColor.COLOR_SUCCESS)
            self.on_done_or_skipped.emit(self.id)
            self.is_skipped_or_done = True
            return True

    def _create_default_dataset(self):
        self.print_info.emit(
            self.tr("Create the default dataset {}").format(
                wizard_tools.DEFAULT_DATASETNAME
            ),
            LogColor.COLOR_INFO,
        )
        db_connector = db_utils.get_db_connector(self.configuration)

        default_dataset_tid = None
        default_datasets_info_tids = [
            datasets_info["t_id"]
            for datasets_info in db_connector.get_datasets_info()
            if datasets_info["datasetname"] == wizard_tools.DEFAULT_DATASETNAME
        ]
        if default_datasets_info_tids:
            default_dataset_tid = default_datasets_info_tids[0]
        else:
            status, message = db_connector.create_dataset(
                wizard_tools.DEFAULT_DATASETNAME
            )
            self.print_info.emit(message, LogColor.COLOR_INFO)
            if status:
                default_datasets_info_tids = [
                    datasets_info["t_id"]
                    for datasets_info in db_connector.get_datasets_info()
                    if datasets_info["datasetname"] == wizard_tools.DEFAULT_DATASETNAME
                ]
                if default_datasets_info_tids:
                    default_dataset_tid = default_datasets_info_tids[0]

        if default_dataset_tid is not None:
            for topic_record in db_connector.get_topics_info():
                status, message = db_connector.create_basket(
                    default_dataset_tid,
                    ".".join([topic_record["model"], topic_record["topic"]]),
                )
                self.print_info.emit(
                    self.tr("- {}").format(message), LogColor.COLOR_INFO
                )
        else:
            self.print_info.emit(
                self.tr(
                    "No default dataset created ({}) - do it manually in the dataset manager."
                ).format(message),
                LogColor.COLOR_FAIL,
            )
