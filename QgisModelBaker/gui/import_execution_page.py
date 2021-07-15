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
import copy

from QgisModelBaker.gui.panel.import_session_panel import ImportSessionPanel
from QgisModelBaker.gui.panel.log_panel import LogPanel

from QgisModelBaker.libili2db.ilicache import (
    IliCache, 
    ModelCompleterDelegate
)

from QgisModelBaker.libili2db.globals import DbIliMode, displayDbIliMode, DbActionType
from ..libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ..libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from ..libili2db import iliimporter

from qgis.PyQt.QtWidgets import (
    QWizardPage,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QLayout,
    QMessageBox,
    QAction,
    QToolButton
)

from qgis.PyQt.QtGui import (
    QColor,
    QDesktopServices,
    QValidator
)
from qgis.core import (
    QgsProject,
    QgsCoordinateReferenceSystem,
    Qgis
)

from qgis.PyQt.QtCore import (
    QCoreApplication,
    QSettings,
    Qt,
    QLocale,
    QModelIndex,
    QTimer,
    QEventLoop
)
from qgis.gui import (
    QgsMessageBar,
    QgsGui
)

from ..utils import get_ui_class

PAGE_UI = get_ui_class('import_execution.ui')

class ImportExecutionPage(QWizardPage, PAGE_UI):

    def __init__(self, parent):
        QWizardPage.__init__(self, parent)
        
        self.setupUi(self)
        self.setFixedSize(1200,800)
        self.setTitle(self.tr("Execution"))
        self.log_panel = LogPanel()
        layout = self.layout()
        layout.addWidget(self.log_panel)
        self.setLayout(layout)

        self.session_widget_list = []

    def run(self, configuration, import_sessions, data_import = False):
        for key in import_sessions:
            models = import_sessions[key]['models'] if 'models' in import_sessions[key] else []
            dataset = import_sessions[key]['dataset'] if 'dataset' in import_sessions[key] else None
            import_session = ImportSessionPanel(copy.deepcopy(configuration), key, models, dataset, data_import)
            import_session.print_info.connect(self.log_panel.print_info)
            import_session.on_stderr.connect(self.log_panel.on_stderr)
            import_session.on_process_started.connect(self.on_process_started)
            import_session.on_process_finished.connect(self.on_process_finished)
            if import_session not in self.session_widget_list:
                self.session_widget_list.append(import_session)
            print(f'key {key}')

        self.session_layout = QVBoxLayout()
        for session_widget in self.session_widget_list:
            self.session_layout.addWidget(session_widget)
        self.session_layout.addSpacerItem(QSpacerItem(0,self.scroll_area_content.height(), QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.scroll_area_content.setLayout(self.session_layout)

        loop = QEventLoop()
        for session_widget in self.session_widget_list:
            if not session_widget.run():
                session_widget.on_done_or_skipped.connect(lambda: loop.quit())
                loop.exec()

    def on_process_started(self, command):
        self.log_panel.print_info(command, '#000000')
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        if exit_code == 0:
            color = LogPanel.COLOR_SUCCESS
            message = self.tr(
                'Interlis model(s) successfully imported into the database!')
        else:
            color = LogPanel.COLOR_FAIL
            message = self.tr('Finished with errors!')

        self.log_panel.print_info(message, color)