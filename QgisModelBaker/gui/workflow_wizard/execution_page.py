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

import copy

from qgis.PyQt.QtCore import QCoreApplication, QEventLoop
from qgis.PyQt.QtWidgets import (
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

import QgisModelBaker.libs.modelbaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.session_panel import SessionPanel
from QgisModelBaker.libs.modelbaker.utils.globals import DbActionType, LogLevel
from QgisModelBaker.utils import gui_utils

PAGE_UI = gui_utils.get_ui_class("workflow_wizard/execution.ui")


class ExecutionPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title, db_action_type):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent
        self.db_action_type = db_action_type

        self.setupUi(self)
        self.setTitle(title)

        if self.db_action_type == DbActionType.SCHEMA_IMPORT:
            self.description.setText(
                self.tr(
                    "Run the ili2db sessions to make the model imports (or skip to continue)."
                )
            )
        elif self.db_action_type == DbActionType.IMPORT_DATA:
            self.description.setText(
                self.tr(
                    "Run the ili2db sessions to make the data imports (or skip to continue)."
                )
            )
        elif self.db_action_type == DbActionType.EXPORT:
            self.description.setText(
                self.tr(
                    "Run the ili2db session to make the data export (or skip to continue)."
                )
            )

        self.session_widget_list = []
        self.session_status = []
        self.run_command_button.setEnabled(False)
        self.run_command_button.clicked.connect(self._run)
        self.is_complete = False
        self.pending_sessions = []

    def isComplete(self):
        return self.is_complete

    def setComplete(self, complete):
        self.is_complete = complete
        self.run_command_button.setDisabled(complete)
        self.completeChanged.emit()

    def nextId(self):
        if self.db_action_type == DbActionType.EXPORT:
            return -1
        return self.workflow_wizard.next_id()

    def setup_sessions(self, configuration, sessions):
        new_sessions = []

        for key in sessions:
            models = sessions[key]["models"] if "models" in sessions[key] else []
            datasets = (
                sessions[key]["datasets"] if "datasets" in sessions[key] else None
            )
            baskets = sessions[key]["baskets"] if "baskets" in sessions[key] else None
            export_models = (
                sessions[key]["export_models"]
                if "export_models" in sessions[key]
                else None
            )
            delete_data = (
                sessions[key]["delete_data"] if "delete_data" in sessions[key] else None
            )

            skipped_session_widget = self._find_skipped_session_widget(
                (
                    key,
                    models,
                    datasets,
                    baskets,
                    export_models,
                    db_utils.get_schema_identificator_from_configuration(configuration),
                    delete_data,
                )
            )
            if skipped_session_widget:
                new_sessions.append(skipped_session_widget)
            else:
                session = SessionPanel(
                    copy.deepcopy(configuration),
                    key,
                    models,
                    datasets,
                    baskets,
                    export_models,
                    self.db_action_type,
                    delete_data,
                )
                session.on_done_or_skipped.connect(self._on_done_or_skipped_received)
                session.print_info.connect(self.workflow_wizard.log_panel.print_info)
                session.on_stdout.connect(
                    self.workflow_wizard.log_panel.print_stdout_info
                )
                session.on_process_started.connect(self._on_process_started)
                session.on_process_finished.connect(self._on_process_finished)
                new_sessions.append(session)

        self.session_widget_list = new_sessions

        session_layout = QVBoxLayout()
        content = QWidget()
        for session_widget in self.session_widget_list:
            session_layout.addWidget(session_widget)
        session_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Expanding)
        )
        content.setLayout(session_layout)
        self.scroll_area.setWidget(content)

        self.pending_sessions = [
            session.id
            for session in self.session_widget_list
            if not session.is_skipped_or_done
        ]
        self.setComplete(not self.pending_sessions)

    def _find_skipped_session_widget(self, id):
        for session_widget in self.session_widget_list:
            if id == session_widget.id and session_widget.is_skipped_or_done:
                return session_widget
        return None

    def _on_done_or_skipped_received(self, id, state=True):
        if state and id in self.pending_sessions:
            self.pending_sessions.remove(id)
        if not state and id not in self.pending_sessions:
            self.pending_sessions.append(id)
        self.setComplete(not self.pending_sessions)

    def _run(self):
        loop = QEventLoop()
        for session_widget in self.session_widget_list:
            session_widget.on_done_or_skipped.connect(lambda: loop.quit())
            # fall in a loop on fail untill the user skipped it or it has been successful
            if not session_widget.run():
                loop.exec()

    def _on_process_started(self, command):
        self.workflow_wizard.log_panel.print_info(command, LogLevel.INFO)
        QCoreApplication.processEvents()

    def _on_process_finished(self, exit_code, result):
        if exit_code == 0:
            message = "Finished with success."
            level = LogLevel.SUCCESS
            if self.db_action_type == DbActionType.SCHEMA_IMPORT:
                message = self.tr(
                    "INTERLIS model(s) successfully imported into the database!"
                )
            elif self.db_action_type == DbActionType.IMPORT_DATA:
                message = self.tr(
                    "Transfer data successfully imported into the database!"
                )
            elif self.db_action_type == DbActionType.EXPORT:
                message = self.tr("Data successfully exported into transfer file!")
        else:
            level = LogLevel.FAIL
            message = self.tr("Finished with errors!")

        self.workflow_wizard.log_panel.print_info(message, level)

    def help_text(self):
        logline = self.tr("Run, skip or edit the required ili2db sessions...")
        help_paragraphs = self.tr(
            """
        <p align="justify">With the small triangle next to run, you can expand the possiblities.</p>
         <p align="justify">Usually the required ili2db sessions are detected, you should not need to <b>skip</b> them.</p>
         <p align="justify">You might need to <b>edit</b> the command in case your system requires it. But you would know, if you need to.</p>
         <p align="justify">A pretty common use case is, that you want to import <b>invalid</b> data, to fix 'em in QGIS.<br />
         So you can create schemas <b>without constraints</b> and/or import data <b>without validation</b>.</p>
        """
        )
        docutext = self.tr(
            'Find more information about this in the <a href="https://opengisch.github.io/QgisModelBaker/user_guide/import_workflow/#4-run-ili2db-sessions">documentation</a>...'
        )
        return logline, help_paragraphs, docutext
