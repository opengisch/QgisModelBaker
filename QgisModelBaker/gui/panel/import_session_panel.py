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

WIDGET_UI = get_ui_class('import_session_panel.ui')

class ImportSessionPanel(QWidget, WIDGET_UI):

    print_info = pyqtSignal(str, str)
    on_stderr = pyqtSignal(str)
    on_process_started = pyqtSignal(str)
    on_process_finished = pyqtSignal(int, int)
    on_done_or_skipped = pyqtSignal()

    def __init__(self, general_configuration, file, models, dataset, data_import, parent = None):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        # set up the gui
        self.create_text = self.tr('Run')
        self.set_button_to_create_action = QAction(self.create_text, None)
        self.set_button_to_create_action.triggered.connect(self.set_button_to_create)

        self.create_without_constraints_text = self.tr('Run without constraints')
        self.set_button_to_create_without_constraints_action = QAction(self.create_without_constraints_text, None)
        self.set_button_to_create_without_constraints_action.triggered.connect(self.set_button_to_create_without_constraints)

        self.edit_command_action = QAction(self.tr('Edit ili2db command'), None)
        self.edit_command_action.triggered.connect(self.edit_command)

        self.skip_action = QAction(self.tr('Skip'), None)
        self.skip_action.triggered.connect(self.skip)

        self.create_tool_button.addAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.addAction(self.skip_action)
        self.create_tool_button.setText(self.create_text)
        self.create_tool_button.clicked.connect(self.run)

        # set up the values
        self.configuration = general_configuration
        self.data_import = data_import
        if not self.data_import:
            self.configuration.ilifile = ''        
            if file != 'repository':
                self.configuration.ilifile = file
            self.configuration.ilimodels = ';'.join(models)
            self.info_label.setText( self.tr('Import {}').format(' ,'.join(models)))
        else:
            self.configuration.xtffile = file
            self.configuration.ilimodels = ';'.join(models)
            self.info_label.setText( self.tr('Import {} of {}').format(' ,'.join(models), file))

        self.db_simple_factory = DbSimpleFactory()

    def set_button_to_create(self):
        """
        Changes the text of the button to create (with validation) and sets the validate_data to true.
        So on clicking the button the creation will start with validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.configuration.disable_validations = False
        self.create_tool_button.removeAction(self.set_button_to_create_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_text)

    def set_button_to_create_without_constraints(self):
        """
        Changes the text of the button to create without validation and sets the validate_data to false.
        So on clicking the button the creation will start without validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.configuration.disable_validations = True
        self.create_tool_button.removeAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_without_constraints_text)

    def skip(self):
        self.setDisabled(True)
        self.print_info.emit(self.tr('Import skipped!\n'), LogPanel.COLOR_INFO)
        self.on_done_or_skipped.emit()

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

    def run(self, edited_command = None):
        
        importer = iliimporter.Importer(dataImport=self.data_import)
        importer.tool = self.configuration.tool
        importer.configuration = self.configuration
        
        db_factory = self.db_simple_factory.create_factory(self.configuration.tool)

        with OverrideCursor(Qt.WaitCursor):
            self.progress_bar.setValue(10)
            self.setDisabled(True)

            importer.stdout.connect(lambda str: self.print_info.emit(str, LogPanel.COLOR_INFO))
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
            
            self.progress_bar.setValue(100)
            self.print_info.emit(self.tr('Import done!\n'), LogPanel.COLOR_SUCCESS)
            self.on_done_or_skipped.emit()
            return True
        
            