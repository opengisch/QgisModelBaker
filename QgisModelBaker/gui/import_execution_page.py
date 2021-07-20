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

from qgis.PyQt.QtCore import (
    QCoreApplication,
    QEventLoop
)

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from qgis.gui import (
    QgsMessageBar,
    QgsGui
)

from QgisModelBaker.gui.panel.import_session_panel import ImportSessionPanel
from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from ..libili2db import iliimporter

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_execution.ui')


class ImportExecutionPage(QWizardPage, PAGE_UI):

    def __init__(self, parent):
        QWizardPage.__init__(self, parent)

        self.import_wizard = parent
        self.setupUi(self)
        self.setFixedSize(800, 600)
        self.setTitle(self.tr("Execution"))

        self.session_widget_list = []
        self.run_command_button.setEnabled(False)
        self.run_command_button.clicked.connect(self.run)

    def find_existing_session_widget(self, id):
        for session_widget in self.session_widget_list:
            if id == session_widget.id:
                return session_widget
        return None

    def setup_sessions(self, configuration, import_sessions, data_import=False):
        new_sessions = []

        for key in import_sessions:
            models = import_sessions[key]['models'] if 'models' in import_sessions[key] else [
            ]
            dataset = import_sessions[key]['dataset'] if 'dataset' in import_sessions[key] else None

            existing_widget = self.find_existing_session_widget((key, models))
            if existing_widget:
                new_sessions.append(existing_widget)
            else:
                import_session = ImportSessionPanel(copy.deepcopy(
                    configuration), key, models, dataset, data_import)
                import_session.print_info.connect(
                    self.import_wizard.log_panel.print_info)
                import_session.on_stderr.connect(
                    self.import_wizard.log_panel.on_stderr)
                import_session.on_process_started.connect(
                    self.on_process_started)
                import_session.on_process_finished.connect(
                    self.on_process_finished)
                new_sessions.append(import_session)

        self.session_widget_list = new_sessions
        session_layout = QVBoxLayout()
        content = QWidget()
        for session_widget in self.session_widget_list:
            session_layout.addWidget(session_widget)
        session_layout.addSpacerItem(QSpacerItem(
            0, content.height(), QSizePolicy.Expanding, QSizePolicy.Minimum))
        content.setLayout(session_layout)
        self.scroll_area.setWidget(content)

        self.run_command_button.setEnabled(len(self.session_widget_list))

    def run(self):
        loop = QEventLoop()
        for session_widget in self.session_widget_list:
            session_widget.on_done_or_skipped.connect(lambda: loop.quit())
            # fall in a loop on fail untill the user skipped it or it has been successful
            if not session_widget.run():
                loop.exec()
            session_widget.on_done_or_skipped.disconnect()

    def on_process_started(self, command):
        self.import_wizard.log_panel.print_info(command, '#000000')
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        if exit_code == 0:
            color = LogPanel.COLOR_SUCCESS
            message = self.tr(
                'Interlis model(s) successfully imported into the database!')
        else:
            color = LogPanel.COLOR_FAIL
            message = self.tr('Finished with errors!')

        self.import_wizard.log_panel.print_info(message, color)

    def nextId(self):
        return self.import_wizard.next_id()
