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

from QgisModelBaker.gui.panel.import_session_panel import ImportSessionPanel

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
    QSizePolicy,
    QGridLayout,
    QLayout,
    QMessageBox,
    QAction,
    QToolButton
)

from QgisModelBaker.libili2db.ili2dbutils import color_log_text, JavaNotFoundError
from QgisModelBaker.utils.qt_utils import (
    OverrideCursor
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

        self.setTitle(self.tr("Execution"))

        self.db_simple_factory = DbSimpleFactory()

        self.txtStdout = parent.txtStdout
        self.setFixedSize(1200,800)

    def run(self, configuration, import_sessions, edited_command=None):     
        self.session_layout = QGridLayout()
        for key in import_sessions:
            import_session = ImportSessionPanel(configuration, key, import_sessions[key]['models'])
            self.session_layout.addWidget(import_session)
            self.scroll_area_content.setLayout(self.session_layout) 

    def print_info(self, text):
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.append(text)
        QCoreApplication.processEvents()

    def on_stderr(self, text):
        color_log_text(text, self.txtStdout)
        QCoreApplication.processEvents()

    def show_message(self, level, message):
        if level == Qgis.Warning:
            self.bar.pushMessage(message, Qgis.Info, 10)
        elif level == Qgis.Critical:
            self.bar.pushMessage(message, Qgis.Warning, 10)

    def on_process_started(self, command):
        self.txtStdout.setTextColor(QColor('#000000'))
        self.txtStdout.setText(command)
        QCoreApplication.processEvents()

    def on_process_finished(self, exit_code, result):
        color = '#004905' if exit_code == 0 else '#aa2222'
        self.txtStdout.setTextColor(QColor(color))
        self.txtStdout.append(self.tr('Finished ({})'.format(exit_code)))
        if result == iliimporter.Importer.SUCCESS:
            self.command += '\nSUCCESS!\n'
        else:
            self.command += '\nFAIL!\n'
            self.comand_label.setText(str(self.command ))
