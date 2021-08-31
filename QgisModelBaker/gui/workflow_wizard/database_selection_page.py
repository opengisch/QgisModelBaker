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

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QWizardPage

from QgisModelBaker.libili2db.globals import DbActionType, DbIliMode, displayDbIliMode
from QgisModelBaker.utils import db_utils

from ...libqgsprojectgen.db_factory.db_simple_factory import DbSimpleFactory
from ...utils import get_ui_class

PAGE_UI = get_ui_class("workflow_wizard/database_selection.ui")


class DatabaseSelectionPage(QWizardPage, PAGE_UI):
    def __init__(self, parent, title, db_action_type):
        QWizardPage.__init__(self, parent)

        self.workflow_wizard = parent
        self.db_action_type = db_action_type

        self.setupUi(self)
        self.setTitle(title)

        # in this context we use GENERATE for the project generation and the IMPORT_DATA for the schema import (and the data import)
        if db_action_type == DbActionType.GENERATE:
            self.description.setText(
                self.tr(
                    "Select an existing database you want to generate a QGIS project from."
                )
            )
        elif db_action_type == DbActionType.EXPORT:
            self.description.setText(
                self.tr("Select an existing database you want to export from.")
            )
        else:
            self.description.setText(
                self.tr("Choose the database you want to create or import to.")
            )

        self.type_combo_box.clear()
        self._lst_panel = dict()
        self.db_simple_factory = DbSimpleFactory()

        for db_id in self.db_simple_factory.get_db_list(False):
            self.type_combo_box.addItem(displayDbIliMode[db_id], db_id)
            db_factory = self.db_simple_factory.create_factory(db_id)
            item_panel = db_factory.get_config_panel(self, db_action_type)
            self._lst_panel[db_id] = item_panel
            self.db_layout.addWidget(item_panel)

        self.type_combo_box.currentIndexChanged.connect(self._type_changed)

    def _type_changed(self):

        ili_mode = self.type_combo_box.currentData()
        db_id = ili_mode & ~DbIliMode.ili

        self.db_wrapper_group_box.setTitle(displayDbIliMode[db_id])

        # Refresh panels
        for key, value in self._lst_panel.items():
            is_current_panel_selected = db_id == key
            value.setVisible(is_current_panel_selected)
            if is_current_panel_selected:
                value._show_panel()

    def restore_configuration(self, configuration):
        # takes settings from QSettings and provides it to the gui (not the configuration)
        # it needs the configuration - this is the same for Schema or Data Config
        settings = QSettings()

        for db_id in self.db_simple_factory.get_db_list(False):
            db_factory = self.db_simple_factory.create_factory(db_id)
            config_manager = db_factory.get_db_command_config_manager(configuration)
            config_manager.load_config_from_qsettings()
            self._lst_panel[db_id].set_fields(configuration)

        mode = settings.value("QgisModelBaker/importtype")
        mode = DbIliMode[mode] if mode else self.db_simple_factory.default_database
        mode = mode & ~DbIliMode.ili

        self.type_combo_box.setCurrentIndex(self.type_combo_box.findData(mode))
        self._type_changed()

    def update_configuration(self, configuration):
        # takes settings from the GUI and provides it to the configuration
        mode = self.type_combo_box.currentData()
        self._lst_panel[mode].get_fields(configuration)
        configuration.tool = mode
        configuration.db_ili_version = db_utils.db_ili_version(configuration)

    def save_configuration(self, updated_configuration):
        # puts it to QSettings
        settings = QSettings()
        settings.setValue(
            "QgisModelBaker/importtype", self.type_combo_box.currentData().name
        )
        mode = self.type_combo_box.currentData()
        db_factory = self.db_simple_factory.create_factory(mode)
        config_manager = db_factory.get_db_command_config_manager(updated_configuration)
        config_manager.save_config_in_qsettings()

    def nextId(self):
        return self.workflow_wizard.next_id()
