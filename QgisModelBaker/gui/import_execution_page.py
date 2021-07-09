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

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.txtStdout.setLayout(QGridLayout())
        self.txtStdout.layout().setContentsMargins(0, 0, 0, 0)
        self.txtStdout.layout().addWidget(self.bar, 0, 0, Qt.AlignTop)

        self.command = ''


    def run(self, configuration, import_sessions, edited_command=None):
        # draft
        commands = ''
        for key in import_sessions:

            configuration.ilifile = ''
            if key != 'repository':
                configuration.ilifile = key

            configuration.ilimodels = ';'.join(import_sessions[key]['models'])
            importer = iliimporter.Importer()
            importer.tool = configuration.tool
            importer.configuration = configuration
            command = importer.command(True)

            self.command += '\n'+command
            self.comand_label.setText(str(self.command ))

            db_factory = self.db_simple_factory.create_factory(configuration.tool)

            try:
                # raise warning when the schema or the database file already exists
                config_manager = db_factory.get_db_command_config_manager(configuration)
                db_connector = db_factory.get_db_connector(
                    config_manager.get_uri(configuration.db_use_super_login) or config_manager.get_uri(), configuration.dbschema)

                if db_connector.db_or_schema_exists():
                    warning_box = QMessageBox(self)
                    warning_box.setIcon(QMessageBox.Information)
                    warning_title = self.tr("{} already exists").format(
                        db_factory.get_specific_messages()['db_or_schema']
                    ).capitalize()
                    warning_box.setWindowTitle(warning_title)
                    warning_box.setText(self.tr("{warning_title}:\n{db_or_schema_name}\n\nDo you want to "
                                                "import into the existing {db_or_schema}?").format(
                        warning_title=warning_title,
                        db_or_schema=db_factory.get_specific_messages()['db_or_schema'].capitalize(),
                        db_or_schema_name=configuration.dbschema or config_manager.get_uri()
                    ))
                    warning_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    warning_box_result = warning_box.exec_()
                    if warning_box_result == QMessageBox.No:
                        return
            except (DBConnectorError, FileNotFoundError):
                # we don't mind when the database file is not yet created
                pass

            # create schema with superuser
            res, message = db_factory.pre_generate_project(configuration)
            if not res:
                self.txtStdout.setText(message)
                return

            with OverrideCursor(Qt.WaitCursor):
                #self.progress_bar.show()
                #self.progress_bar.setValue(0)

                self.txtStdout.setTextColor(QColor('#000000'))

                importer = iliimporter.Importer()
                importer.tool = configuration.tool
                importer.configuration = configuration
                importer.stdout.connect(self.print_info)
                importer.stderr.connect(self.on_stderr)
                importer.process_started.connect(self.on_process_started)
                importer.process_finished.connect(self.on_process_finished)
                try:
                    if importer.run(edited_command) != iliimporter.Importer.SUCCESS:
                        #self.progress_bar.hide()
                        return
                except JavaNotFoundError as e:
                    self.txtStdout.setTextColor(QColor('#000000'))
                    self.txtStdout.setText(e.error_string)
                    #self.progress_bar.hide()
                    return

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
