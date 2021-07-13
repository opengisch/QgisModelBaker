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

from ...utils import get_ui_class
from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...libqgsprojectgen.dbconnector.db_connector import DBConnectorError
from ...libili2db import iliimporter

from QgisModelBaker.gui.edit_command import EditCommandDialog

WIDGET_UI = get_ui_class('import_session_panel.ui')

class ImportSessionPanel(QWidget, WIDGET_UI):

    def __init__(self, general_configuration, file, models, parent = None):
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

        self.create_tool_button.addAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_text)
        self.create_tool_button.clicked.connect(self.run)

        # set up the values
        self.configuration = general_configuration
        self.configuration.ilifile = ''
        
        if file != 'repository':
            self.configuration.ilifile = file

        self.configuration.ilimodels = ';'.join(models)

        self.info_label.setText( self.tr('Import {}').format(' ,'.join(models)))

    def set_button_to_create(self):
        """
        Changes the text of the button to create (with validation) and sets the validate_data to true.
        So on clicking the button the creation will start with validation.
        The buttons actions are changed to be able to switch the with-validation mode.
        """
        self.create_constraints = True
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
        self.create_constraints = False
        self.create_tool_button.removeAction(self.set_button_to_create_without_constraints_action)
        self.create_tool_button.removeAction(self.edit_command_action)
        self.create_tool_button.addAction(self.set_button_to_create_action)
        self.create_tool_button.addAction(self.edit_command_action)
        self.create_tool_button.setText(self.create_without_constraints_text)

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

    def run(self, edited_command):
        '''
        importer = iliimporter.Importer()
        importer.tool = self.configuration.tool
        importer.configuration = self.configuration
        self.info_label.setText(importer.command(True))

        db_factory = self.db_simple_factory.create_factory(importer.configuration.tool)

        try:
            # raise warning when the schema or the database file already exists
            config_manager = db_factory.get_db_command_config_manager(importer.configuration)
            db_connector = db_factory.get_db_connector(
                config_manager.get_uri(importer.configuration.db_use_super_login) or config_manager.get_uri(), importer.configuration.dbschema)

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
        res, message = db_factory.pre_generate_project(importer.configuration)
        if not res:
            self.txtStdout.setText(message)
            return

        with OverrideCursor(Qt.WaitCursor):
            #self.progress_bar.show()
            #self.progress_bar.setValue(0)

            self.txtStdout.setTextColor(QColor('#000000'))

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
                '''
