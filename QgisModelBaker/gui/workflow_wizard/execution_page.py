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

import copy

from qgis.PyQt.QtCore import QCoreApplication, QEventLoop
from qgis.PyQt.QtWidgets import (
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QWizardPage,
)

import QgisModelBaker.utils.db_utils as db_utils
from QgisModelBaker.gui.panel.session_panel import SessionPanel
from QgisModelBaker.libili2db.globals import DbActionType

from ...utils import ui
from ...utils.ui import LogColor

PAGE_UI = ui.get_ui_class("workflow_wizard/execution.ui")


class ExecutionPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title, db_action_type):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent
        self.db_action_type = db_action_type

        self.setupUi(self)
        self.setTitle(title)

        # in this context we use GENERATE for the schema import and IMPORT_DATA for the data import
        if self.db_action_type == DbActionType.GENERATE:
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

    def setup_sessions(self, configuration, import_sessions):
        new_sessions = []

        for key in import_sessions:
            models = (
                import_sessions[key]["models"]
                if "models" in import_sessions[key]
                else []
            )
            datasets = (
                import_sessions[key]["datasets"]
                if "datasets" in import_sessions[key]
                else None
            )

            skipped_session_widget = self._find_skipped_session_widget(
                (
                    key,
                    models,
                    datasets,
                    db_utils.get_schema_identificator_from_configuration(configuration),
                )
            )
            if skipped_session_widget:
                new_sessions.append(skipped_session_widget)
            else:
                import_session = SessionPanel(
                    copy.deepcopy(configuration),
                    key,
                    models,
                    datasets,
                    self.db_action_type,
                )
                import_session.on_done_or_skipped.connect(
                    self._on_done_or_skipped_received
                )
                import_session.print_info.connect(
                    self.workflow_wizard.log_panel.print_info
                )
                import_session.on_stderr.connect(
                    self.workflow_wizard.log_panel.on_stderr
                )
                import_session.on_process_started.connect(self._on_process_started)
                import_session.on_process_finished.connect(self._on_process_finished)
                new_sessions.append(import_session)

        self.session_widget_list = new_sessions

        session_layout = QVBoxLayout()
        content = QWidget()
        for session_widget in self.session_widget_list:
            session_layout.addWidget(session_widget)
        session_layout.addSpacerItem(
            QSpacerItem(0, content.height(), QSizePolicy.Expanding, QSizePolicy.Minimum)
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

    def _on_done_or_skipped_received(self, id):
        self.pending_sessions.remove(id)
        if not self.pending_sessions:
            self.setComplete(True)

    def _run(self):
        loop = QEventLoop()
        for session_widget in self.session_widget_list:
            session_widget.on_done_or_skipped.connect(lambda: loop.quit())
            # fall in a loop on fail untill the user skipped it or it has been successful
            if not session_widget.run():
                loop.exec()

    def _on_process_started(self, command):
        self.workflow_wizard.log_panel.print_info(command, "#000000")
        QCoreApplication.processEvents()

    def _on_process_finished(self, exit_code, result):
        if exit_code == 0:
            message = "Finished with success."
            color = LogColor.COLOR_SUCCESS
            if self.db_action_type == DbActionType.GENERATE:
                message = self.tr(
                    "Interlis model(s) successfully imported into the database!"
                )
            elif self.db_action_type == DbActionType.IMPORT_DATA:
                message = self.tr(
                    "Transfer data successfully imported into the database!"
                )
            elif self.db_action_type == DbActionType.EXPORT:
                message = self.tr("Data successfully exported into transfer file!")
        else:
            color = LogColor.COLOR_FAIL
            message = self.tr("Finished with errors!")

        self.workflow_wizard.log_panel.print_info(message, color)
